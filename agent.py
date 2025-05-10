import importlib.util
import json
import os
import sys
import traceback
from typing import List  # Only keep what we actually use

import requests

# Import for prompt_toolkit
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

# We'll use direct API calls instead of the OpenAI client
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

from tools.file_operations.create_empty_file import create_empty_file
from tools.file_operations.move_files import move_files

# Import tool functions from reorganized directories
from tools.file_operations.read_file_content import read_file_content
from tools.file_operations.write_to_file import write_to_file

# Other tools will be imported dynamically through the directory scanning mechanism

# --- Rich Console Setup for Colorful Output ---
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "command": "bold magenta",
        "prompt": "green",
        "system": "bright_blue",
        "user": "bright_white",
        "tool": "bright_yellow",
        "assistant": "bright_green",
    }
)

console = Console(theme=custom_theme, highlight=True)

# --- Configuration ---
OPEN_ROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
LLM_MODEL = "google/gemini-2.5-flash-preview"

# Context Management Configuration
MAX_HISTORY_ITEMS = 30  # Keep this many recent messages plus system prompt
HISTORY_FILE = ".agent_history"


# --- Helper Function for Context Pruning ---
def prune_messages(messages_list: List[dict], max_items: int) -> List[dict]:
    """
    Prunes the messages list to keep the system prompt and a window of recent messages.
    """
    if len(messages_list) <= max_items + 1:
        return messages_list

    system_prompt = [messages_list[0]]
    recent_messages = messages_list[-max_items:]

    pruned_list = system_prompt + recent_messages
    console.print(
        f"[info]--- Context Pruning: Reduced message history from {len(messages_list)} to {len(pruned_list)} items. ---[/info]"
    )
    return pruned_list


# --- Direct OpenRouter API client ---
def call_openrouter_api(messages, model, tools=None, tool_choice=None):
    """
    Make a direct API call to OpenRouter without using the OpenAI client.
    Returns a response with choices that have tool_calls if present.
    """
    endpoint = f"{OPENROUTER_API_BASE}/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"model": model, "messages": messages}

    if tools:
        payload["tools"] = tools

    if tool_choice:
        payload["tool_choice"] = tool_choice

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=90)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        console.print(f"[error]API Request Error: {e}[/error]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_body = e.response.json()
                console.print(f"[error]Error details: {error_body}[/error]")
            except Exception as json_err:
                console.print(f"[error]Error parsing response: {json_err}[/error]")
                console.print(
                    f"[error]Error status code: {e.response.status_code}[/error]"
                )
                console.print(f"[error]Error text: {e.response.text}[/error]")
        raise e


# --- Dynamic Tool Discovery and Loading ---
def find_all_tool_modules():
    """Scan all subdirectories in the tools directory for Python modules with get_tool_definition"""
    all_tool_modules = {}
    tools_dir = "tools"

    if not os.path.exists(tools_dir):
        console.print(
            f"[warning]Warning: Tools directory '{tools_dir}' not found.[/warning]"
        )
        return all_tool_modules

    # First, add tools directory itself to sys.path
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)

    # Function to explore a directory and find tool modules
    def explore_dir(directory):
        modules_found = {}

        # List all Python files in this directory
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)

            # If it's a directory with __init__.py, explore it recursively
            if os.path.isdir(item_path) and os.path.exists(
                os.path.join(item_path, "__init__.py")
            ):
                # Recursively explore the subdirectory and add its modules
                sub_modules = explore_dir(item_path)
                modules_found.update(sub_modules)

            # If it's a Python file, try to load it
            elif item.endswith(".py") and item != "__init__.py":
                # Get the module name without .py extension
                module_name = item[:-3]

                # Calculate the full module path
                rel_path = os.path.relpath(
                    os.path.dirname(item_path), start=os.getcwd()
                )
                full_module_path = f"{rel_path.replace(os.path.sep, '.')}.{module_name}"

                try:
                    # Use importlib to import the module
                    module = importlib.import_module(full_module_path)

                    # Check if it has the get_tool_definition function
                    if hasattr(module, "get_tool_definition") and callable(
                        module.get_tool_definition
                    ):
                        # Store the module with its function name for later access
                        function_name = None

                        # Try to determine the function name from the tool definition
                        try:
                            tool_def = module.get_tool_definition()
                            if isinstance(tool_def, dict) and "function" in tool_def:
                                function_name = tool_def["function"].get("name")
                        except Exception:
                            pass

                        # If we couldn't get the name, use the module name
                        if not function_name:
                            function_name = module_name

                        modules_found[function_name] = (module, full_module_path)
                except Exception as e:
                    console.print(
                        f"[warning]Could not load module {full_module_path}: {e}[/warning]"
                    )

        return modules_found

    # Start the exploration at the tools directory
    all_tool_modules = explore_dir(tools_dir)

    # Remove tools directory from sys.path
    if tools_dir in sys.path:
        sys.path.remove(tools_dir)

    return all_tool_modules


# --- Tool Definitions for LLM (Dynamically Loaded) ---
def get_tool_definitions():
    """Get all tool definitions from available modules"""
    tool_definitions = []
    tool_modules = find_all_tool_modules()

    for function_name, (module, module_path) in tool_modules.items():
        try:
            if hasattr(module, "get_tool_definition") and callable(
                module.get_tool_definition
            ):
                tool_def = module.get_tool_definition()
                # Add to list in appropriate format
                if isinstance(tool_def, list):
                    tool_definitions.extend(tool_def)
                else:
                    tool_definitions.append(tool_def)
                console.print(
                    f"[success]Loaded tool definition for '{function_name}' from {module_path}[/success]"
                )
            else:
                console.print(
                    f"[warning]Module {module_path} has no get_tool_definition function[/warning]"
                )
        except Exception as e:
            console.print(
                f"[error]Error loading tool definition from {module_path}: {e}[/error]"
            )
            traceback.print_exc()

    return tool_definitions


def get_available_functions():
    """Create a dictionary mapping function names to their callable implementations"""
    available_functions = {}
    tool_modules = find_all_tool_modules()

    # First, add our explicitly imported functions
    available_functions.update(
        {
            "read_file_content": read_file_content,
            "write_to_file": write_to_file,
            "create_empty_file": create_empty_file,
            "move_files": move_files,
        }
    )

    # Then add dynamically discovered functions
    for function_name, (module, _) in tool_modules.items():
        # Check if the module has a function with the same name as the tool
        if hasattr(module, function_name) and callable(getattr(module, function_name)):
            available_functions[function_name] = getattr(module, function_name)

    return available_functions


def display_logo():
    logo = """
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║   🤖 File System Agent with AI Assistance 🤖  ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
    """
    console.print(Panel(logo, border_style="bright_blue", expand=False))


def display_available_tools():
    """Display all available tools in a nice table"""
    tools_table = Table(title="📋 Available Tools", border_style="bright_blue")
    tools_table.add_column("Tool Name", style="bright_cyan")
    tools_table.add_column("Description", style="bright_white")
    tools_table.add_column("Category", style="bright_magenta")

    # Get all tool definitions
    tool_defs = get_tool_definitions()

    # Categorize tools
    file_ops_tools = []
    formatting_tools = []
    other_tools = []

    for tool_def in tool_defs:
        if isinstance(tool_def, dict) and "function" in tool_def:
            function_def = tool_def["function"]
            name = function_def.get("name", "Unknown")
            description = function_def.get("description", "No description available")

            # Categorize based on module path
            if "file_operations" in str(tool_def):
                file_ops_tools.append((name, description))
            elif "formatting" in str(tool_def):
                formatting_tools.append((name, description))
            else:
                other_tools.append((name, description))

    # Add file operation tools
    for name, description in file_ops_tools:
        tools_table.add_row(name, description, "File Operations")

    # Add formatting tools
    for name, description in formatting_tools:
        tools_table.add_row(name, description, "Formatting")

    # Add other tools
    for name, description in other_tools:
        tools_table.add_row(name, description, "Miscellaneous")

    console.print(tools_table)


# --- Main Application Logic ---
if __name__ == "__main__":
    # Display a fancy logo
    display_logo()

    if not OPEN_ROUTER_API_KEY:
        console.print(
            "[error]Error: OPENROUTER_API_KEY environment variable is not set.[/error]"
        )
        exit(1)

    console.print(
        Panel.fit(
            "Starting interactive chat with OpenRouter assistant\n"
            "Type '[command]exit[/command]' or '[command]quit[/command]' to end the session\n"
            "File/directory paths for tools are relative to where this script is run",
            title="🚀 Welcome",
            border_style="bright_blue",
        )
    )

    # Display available tools
    display_available_tools()

    # System prompt - shortened slightly to avoid line length issues
    system_content = (
        "You are a helpful assistant for refactoring and managing files. "
        "You can use tools to list directory contents, read files, write content to files, "
        "create empty files, create directories, search for files, or get a diff of proposed changes to a file if needed. "
        "You also have tools to delete files and directories, and move files (with wildcard support). "
        "Paths are relative to the script's current working directory. "
        "Maintain context from previous turns to understand follow-up questions. "
        "\n\nRefactoring/Editing Workflow (VERY IMPORTANT):\n"
        "1. When asked to modify or refactor an existing file, first use `read_file_content` to get its current, full content.\n"
        "2. Based on the user's request, formulate the complete, new, full content of the file as it should be after the changes. This means the entire file, not just the changed parts.\n"
        "3. Then, use the `get_diff_for_proposed_changes` tool. Provide it with the original `file_path` and your complete, new, full `proposed_new_content`.\n"
        "4. Present the diff generated by the tool to the user for review. The diff will be colorized (green for additions, red for deletions) for easier reading in the terminal.\n"
        "5. After presenting the diff, wait for the user's feedback. If the user rejects the changes or asks for different modifications, engage in a dialogue to understand their requirements and, if necessary, repeat steps 2-4.\n"
        "6. If the user confirms the changes (e.g., by saying 'yes', 'proceed', 'apply changes'), then and only then, use the `write_to_file` tool.\n"
        "Do not write only partial changes or just function signatures unless that is the entirety of the intended new file content. If creating a new file, the diff step can show the entire content as new.\n"
        "\n\nFile Movement and Organization:\n"
        "You can use the `move_files` tool to move files or directories, including with wildcard patterns like *.py or data/*.csv. "
        "Be careful when using wildcards and always confirm with the user before executing operations that might affect multiple files.\n"
        "\n\nRich Output Support:\n"
        "You can use the `rich_output` tool to format your responses with syntax highlighting, markdown rendering, and panels with borders.\n"
        "\n\nSyntax Highlighting:\n"
        "You can use the `syntax_highlight` tool to show the content of code files with proper syntax highlighting."
    )

    messages = [{"role": "system", "content": system_content}]

    # Setup prompt_toolkit session with history
    session = PromptSession(history=FileHistory(HISTORY_FILE))

    while True:
        # Stylish user prompt
        try:
            # Use prompt_toolkit for input with history
            user_prompt = session.prompt("\nYou > ")
        except EOFError:
            # Handle Ctrl+D
            console.print("[success]Exiting chat session. Goodbye![/success]")
            break

        if user_prompt.lower() in ["exit", "quit"]:
            console.print("[success]Exiting chat session. Goodbye![/success]")
            break

        if not user_prompt.strip():
            continue

        current_turn_messages = [{"role": "user", "content": user_prompt}]
        messages.append(current_turn_messages[0])

        messages_for_api = prune_messages(list(messages), MAX_HISTORY_ITEMS)

        try:
            # Show a spinner while waiting for the API response
            with Progress(
                SpinnerColumn(),
                TextColumn("[system]Assistant is thinking...[/system]"),
                transient=True,
            ) as progress:
                progress.add_task("thinking", total=None)

                response_obj = call_openrouter_api(
                    messages=messages_for_api,
                    model=LLM_MODEL,
                    tools=get_tool_definitions(),
                    tool_choice="auto",
                )

            if not (
                response_obj
                and "choices" in response_obj
                and len(response_obj["choices"]) > 0
            ):
                console.print(
                    "[error]Error: Invalid or empty response from API on initial call.[/error]"
                )
                console.print(f"[error]Response object: {response_obj}[/error]")
                messages.pop()
                continue

            response_choice = response_obj["choices"][0]
            if "message" not in response_choice:
                console.print(
                    "[error]Error: API response's first choice has no message.[/error]"
                )
                console.print(f"[error]Response choice: {response_choice}[/error]")
                messages.pop()
                continue

            response_message = response_choice["message"]

            # Store response in messages list
            messages.append(response_message)

            # Check if there are tool calls in the message
            tool_calls = response_message.get("tool_calls", None)

            while tool_calls:
                console.print(
                    Panel(
                        "[tool]LLM wants to call a tool![/tool]",
                        border_style="bright_yellow",
                        expand=False,
                    )
                )

                # Get all available functions
                available_functions = get_available_functions()

                for tool_call in tool_calls:
                    function_data = tool_call.get("function", {})
                    function_name = function_data.get("name", "")
                    function_to_call = available_functions.get(function_name)

                    if function_to_call:
                        function_args_str = function_data.get("arguments", "{}")
                        tool_table = Table(
                            show_header=False, border_style="bright_yellow"
                        )
                        tool_table.add_column("", style="bright_yellow")
                        tool_table.add_column("", style="bright_white")
                        tool_table.add_row(
                            "Function:", f"[command]{function_name}[/command]"
                        )

                        # Format the JSON arguments nicely with syntax highlighting
                        function_args_syntax = Syntax(
                            function_args_str,
                            "json",
                            theme="monokai",
                            line_numbers=False,
                            word_wrap=True,
                        )
                        tool_table.add_row("Arguments:", "")
                        console.print(tool_table)
                        console.print(function_args_syntax)

                        try:
                            function_args = json.loads(function_args_str)
                        except json.JSONDecodeError as e:
                            console.print(
                                f"[error]Error decoding JSON arguments: {e}[/error]"
                            )
                            console.print(
                                f"[error]Problematic string: {function_args_str}[/error]"
                            )
                            tool_result = json.dumps(
                                {"error": "Invalid arguments format received from LLM."}
                            )
                        else:
                            with Progress(
                                SpinnerColumn(),
                                TextColumn(f"[tool]Running {function_name}...[/tool]"),
                                transient=True,
                            ) as progress:
                                task = progress.add_task("running", total=None)
                                tool_result = function_to_call(**function_args)

                            if not isinstance(tool_result, str):
                                console.print(
                                    f"[warning]Warning: Tool '{function_name}' did not return a string. Converting to JSON string.[/warning]"
                                )
                                tool_result = json.dumps(
                                    {
                                        "output": tool_result,
                                        "warning": "Tool function did not return a string.",
                                    }
                                )

                        # Display tool results in a nicely formatted way
                        result_panel = Panel(
                            Syntax(
                                tool_result,
                                "json",
                                theme="monokai",
                                line_numbers=False,
                                word_wrap=True,
                            ),
                            title=f"[tool]Tool Result: {function_name}[/tool]",
                            border_style="bright_yellow",
                            expand=False,
                        )
                        console.print(result_panel)

                        # Add tool response to messages
                        messages.append(
                            {
                                "tool_call_id": tool_call.get("id", ""),
                                "role": "tool",
                                "name": function_name,
                                "content": tool_result,
                            }
                        )
                    else:
                        console.print(
                            f"[error]Error: Unknown function '{function_name}' requested by the LLM.[/error]"
                        )
                        messages.append(
                            {
                                "tool_call_id": tool_call.get("id", ""),
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(
                                    {
                                        "error": f"Function '{function_name}' not found by the client application."
                                    }
                                ),
                            }
                        )

                console.print(
                    Panel(
                        "[system]Sending tool response(s) back to LLM for next step...[/system]",
                        border_style="bright_blue",
                    )
                )
                messages_for_api_tool_response = prune_messages(
                    list(messages), MAX_HISTORY_ITEMS
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn(
                        "[system]Waiting for LLM response after tool call...[/system]"
                    ),
                    transient=True,
                ) as progress:
                    task = progress.add_task("waiting", total=None)
                    response_after_tool_obj = call_openrouter_api(
                        messages=messages_for_api_tool_response, model=LLM_MODEL
                    )

                if not (
                    response_after_tool_obj
                    and "choices" in response_after_tool_obj
                    and len(response_after_tool_obj["choices"]) > 0
                ):
                    console.print(
                        "[error]Error: Invalid or empty response from API after sending tool results.[/error]"
                    )
                    console.print(
                        f"[error]Response object: {response_after_tool_obj}[/error]"
                    )
                    tool_calls = None
                    response_message = None
                    break

                response_choice = response_after_tool_obj["choices"][0]
                if "message" not in response_choice:
                    console.print(
                        "[error]Error: API response's first choice (after tool call) has no message.[/error]"
                    )
                    console.print(f"[error]Response choice: {response_choice}[/error]")
                    tool_calls = None
                    break

                response_message = response_choice["message"]

                # Store response in messages list
                messages.append(response_message)

                # Check if there are more tool calls
                tool_calls = response_message.get("tool_calls", None)

            console.print("\n[assistant]Assistant:[/assistant]")
            if (
                response_message
                and "content" in response_message
                and response_message["content"]
            ):
                # Check if the response contains markdown or code blocks and render them
                if "```" in response_message["content"]:
                    # Process and render markdown with code blocks
                    md = Markdown(response_message["content"])
                    console.print(md)
                else:
                    # Regular text response
                    console.print(response_message["content"])
            else:
                console.print(
                    "[warning](LLM provided no further text content for this turn, or an error occurred preventing a final message)[/warning]"
                )

        except Exception as e:
            console.print(
                f"[error]An unexpected error occurred during interaction: {e}[/error]"
            )
            traceback.print_exc()
            if messages and messages[-1]["role"] == "user":
                console.print(
                    "[warning]--- Popping last user message due to API error to prevent re-submission. ---[/warning]"
                )
                messages.pop()

        console.rule(style="bright_blue")

    console.print("\n[success]Script finished.[/success]")

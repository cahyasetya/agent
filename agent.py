import argparse  # Added for command-line arguments
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
from tools.shared.path_utils import set_focus_path

# Other tools will be imported dynamically through the directory scanning
# mechanism

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
MAX_HISTORY_ITEMS = 10  # Keep this many recent messages plus system prompt
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
    msg = "[info]--- Context Pruning: Reduced message history from "
    msg += f"{len(messages_list)} to {len(pruned_list)} items. ---[/info]"
    console.print(msg)
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
        response = requests.post(
            endpoint, headers=headers, json=payload, timeout=90
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        console.print(f"[error]API Request Error: {e}[/error]")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_body = e.response.json()
                console.print(f"[error]Error details: {error_body}[/error]")
            except Exception as json_err:
                err_msg = f"[error]Error parsing response: {json_err}[/error]"
                console.print(err_msg)
                status_msg = "[error]Error status code: "
                status_msg += f"{e.response.status_code}[/error]"
                console.print(status_msg)
                err_text = f"[error]Error text: {e.response.text}[/error]"
                console.print(err_text)
        raise e


# --- Dynamic Tool Discovery and Loading ---
def find_all_tool_modules():
    """
    Scan all subdirectories in the tools directory for Python modules with
    get_tool_definition
    """
    all_tool_modules = {}
    tools_dir = "tools"

    if not os.path.exists(tools_dir):
        warning_msg = "[warning]Warning: Tools directory '"
        warning_msg += f"{tools_dir}' not found.[/warning]"
        console.print(warning_msg)
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
            init_path = os.path.join(item_path, "__init__.py")
            if os.path.isdir(item_path) and os.path.exists(init_path):
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
                full_module_path = (
                    f"{rel_path.replace(os.path.sep, '.')}.{module_name}"
                )

                try:
                    # Use importlib to import the module
                    module = importlib.import_module(full_module_path)

                    # Check if it has the get_tool_definition function
                    has_tool_def = (hasattr(module, "get_tool_definition") and
                                    callable(module.get_tool_definition))
                    if has_tool_def:
                        # Store the module with its function name for later
                        function_name = None

                        # Try to determine the function name from the tool def
                        try:
                            tool_def = module.get_tool_definition()
                            is_tool_dict = (isinstance(tool_def, dict) and
                                            "function" in tool_def)
                            if is_tool_dict:
                                function_name = tool_def["function"].get("name")
                        except Exception:
                            pass

                        # If we couldn't get the name, use the module name
                        if not function_name:
                            function_name = module_name

                        modules_found[function_name] = (
                            module,
                            full_module_path,
                        )
                except Exception as e:
                    warning_msg = "[warning]Could not load module "
                    warning_msg += f"{full_module_path}: {e}[/warning]"
                    console.print(warning_msg)

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
            has_tool_def = (hasattr(module, "get_tool_definition") and
                            callable(module.get_tool_definition))
            if has_tool_def:
                tool_def = module.get_tool_definition()
                # Add to list in appropriate format
                if isinstance(tool_def, list):
                    tool_definitions.extend(tool_def)
                else:
                    tool_definitions.append(tool_def)
                success_msg = "[success]Loaded tool definition for "
                success_msg += f"'{function_name}' from {module_path}[/success]"
                console.print(success_msg)
            else:
                warning_msg = "[warning]Module {0} has no ".format(module_path)
                warning_msg += "get_tool_definition function[/warning]"
                console.print(warning_msg)
        except Exception as e:
            error_msg = "[error]Error loading tool definition from "
            error_msg += f"{module_path}: {e}[/error]"
            console.print(error_msg)
            traceback.print_exc()

    return tool_definitions


def get_available_functions():
    """
    Create a dictionary mapping function names to their callable implementations
    """
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
        if hasattr(module, function_name) and callable(
            getattr(module, function_name)
        ):
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
            description = function_def.get(
                "description", "No description available"
            )

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
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="File System Agent with AI Assistance."
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Optional path to a directory for the AI to focus on.",
        default=None,
    )
    args = parser.parse_args()
    focus_path = args.path

    # Display a fancy logo
    display_logo()

    if not OPEN_ROUTER_API_KEY:
        error_msg = "[error]Error: OPENROUTER_API_KEY environment variable "
        error_msg += "is not set.[/error]"
        console.print(error_msg)
        exit(1)

    welcome_message = (
        "Starting interactive chat with OpenRouter assistant\n"
        "Type '[command]exit[/command]' or '[command]quit[/command]' to end "
        "the session\n"
        "File/directory paths for tools are relative to where this script is run")
    
    # Process and set the focus path if provided
    if focus_path:
        # Ensure the path is absolute for clarity in the prompt
        abs_focus_path = (
            os.path.abspath(focus_path)
            if not os.path.isabs(focus_path)
            else focus_path
        )
        if os.path.isdir(abs_focus_path):
            info_msg = "\n[info]AI will focus on operations within or related to: "
            info_msg += f"{abs_focus_path}[/info]"
            welcome_message += info_msg

            focus_dir_msg = "Focusing on directory: [bold cyan]{0}".format(
                abs_focus_path)
            focus_dir_msg += "[/bold cyan]"
            console.print(
                Panel.fit(
                    focus_dir_msg,
                    title="🎯 Target Directory",
                    border_style="green",
                    padding=(0, 1),
                )
            )
            
            # Set the focus path in the shared module
            set_focus_path(abs_focus_path)
            
        else:
            warning_msg = "[warning]Warning: The provided path '{0}' ".format(
                focus_path)
            warning_msg += "is not a valid directory. It will be ignored.[/warning]"
            console.print(warning_msg)
            focus_path = None  # Reset if not a valid directory
            set_focus_path(None)  # Ensure focus path is None in the shared module
    else:
        # If no focus path is provided, explicitly set it to None
        set_focus_path(None)

    console.print(
        Panel.fit(
            welcome_message,
            title="🚀 Welcome",
            border_style="bright_blue",
        )
    )

    # Display available tools
    display_available_tools()

    # System prompt - shortened slightly to avoid line length issues
    system_content = (
        "You are a helpful assistant for refactoring and managing files. "
        "You can use tools to list directory contents, read files, write content "
        "to files, create empty files, create directories, search for files, or "
        "get a diff of proposed changes to a file if needed. "
        "You also have tools to delete files and directories, and move files "
        "(with wildcard support). "
        "Paths are relative to the script's current working directory. "
        "Maintain context from previous turns to understand follow-up questions. "
        "\n\nRefactoring/Editing Workflow (VERY IMPORTANT):\n"
        "1. When asked to modify or refactor an existing file, first use "
        "`read_file_content` to get its current, full content.\n"
        "2. Based on the user's request, formulate the complete, new, full content "
        "of the file as it should be after the changes. This means the entire file, "
        "not just the changed parts.\n"
        "3. Then, use the `get_diff_for_proposed_changes` tool. Provide it with the "
        "original `file_path` and your complete, new, full `proposed_new_content`.\n"
        "4. Present the diff generated by the tool to the user for review. The diff "
        "will be colorized (green for additions, red for deletions) for easier "
        "reading in the terminal.\n"
        "5. After presenting the diff, wait for the user's feedback. If the user "
        "rejects the changes or asks for different modifications, engage in a "
        "dialogue to understand their requirements and, if necessary, repeat "
        "steps 2-4.\n"
        "6. If the user confirms the changes (e.g., by saying 'yes', 'proceed', "
        "'apply changes'), then and only then, use the `write_to_file` tool.\n"
        "Do not write only partial changes or just function signatures unless that "
        "is the entirety of the intended new file content. If creating a new file, "
        "the diff step can show the entire content as new.\n"
        "\n\nFile Movement and Organization:\n"
        "You can use the `move_files` tool to move files or directories, including "
        "with wildcard patterns like *.py or data/*.csv. "
        "Be careful when using wildcards and always confirm with the user before "
        "executing operations that might affect multiple files.\n"
        "\n\nRich Output Support:\n"
        "You can use the `rich_output` tool to format your responses with syntax "
        "highlighting, markdown rendering, and panels with borders.\n"
        "\n\nSyntax Highlighting:\n"
        "You can use the `syntax_highlight` tool to show the content of code files "
        "with proper syntax highlighting. Code width should be 80"
        "\n\nFocus Path Behavior:\n"
        "Most file operation tools support a `use_focus_path` parameter which defaults to true. "
        "When true, paths are relative to the focus directory if one is set. "
        "When false, paths are always relative to the current working directory. "
        "This allows flexibility in working with files in different directories."
    )

    if focus_path:
        abs_focus_path = os.path.abspath(
            focus_path
        )  # Already checked if it's a dir
        context_msg = (
            f"\n\nIMPORTANT CONTEXT: The user has specified a focus directory for "
            f"this session: '{abs_focus_path}'. "
            "Please prioritize operations, suggestions, and file paths within or "
            "relative to this directory unless explicitly told otherwise. When "
            "providing file paths in your responses or tool arguments, use paths "
            "relative to the focus directory by default. "
            "If a user refers to 'this directory' or 'the project folder', "
            "assume they mean this focus directory. "
            "By default, all paths provided to tools like read_file_content will "
            "be considered relative to this focus directory. "
            "If the user wants to operate on files outside the focus directory but within "
            "the allowed scope, they can pass use_focus_path=False to the appropriate tool.")
        system_content += context_msg

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

            has_valid_response = (
                response_obj
                and "choices" in response_obj
                and len(response_obj["choices"]) > 0
            )
            if not has_valid_response:
                error_msg = "[error]Error: Invalid or empty response from API "
                error_msg += "on initial call.[/error]"
                console.print(error_msg)
                console.print("[error]Response object: {0}[/error]".format(
                    response_obj))
                messages.pop()
                continue

            response_choice = response_obj["choices"][0]
            if "message" not in response_choice:
                error_msg = "[error]Error: API response's first choice has no "
                error_msg += "message.[/error]"
                console.print(error_msg)
                console.print("[error]Response choice: {0}[/error]".format(
                    response_choice))
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
                            "Function:", "[command]{0}[/command]".format(
                                function_name)
                        )

                        # Format the JSON arguments nicely with syntax
                        # highlighting
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
                            error_msg = "[error]Error decoding JSON arguments: "
                            error_msg += "{0}[/error]".format(e)
                            console.print(error_msg)
                            error_str = "[error]Problematic string: "
                            error_str += "{0}[/error]".format(function_args_str)
                            console.print(error_str)
                            tool_result = json.dumps(
                                {
                                    "error": "Invalid arguments format received "
                                    "from LLM."
                                }
                            )
                        else:
                            with Progress(
                                SpinnerColumn(),
                                TextColumn(
                                    "[tool]Running {0}...[/tool]".format(
                                        function_name)
                                ),
                                transient=True,
                            ) as progress:
                                task = progress.add_task("running", total=None)
                                tool_result = function_to_call(**function_args)

                            if not isinstance(tool_result, str):
                                warning_msg = "[warning]Warning: Tool "
                                warning_msg += "'{0}' did not return ".format(
                                    function_name)
                                warning_msg += "a string. Converting to JSON "
                                warning_msg += "string.[/warning]"
                                console.print(warning_msg)
                                tool_result = json.dumps(
                                    {
                                        "output": tool_result,
                                        "warning": "Tool function did not return "
                                        "a string.",
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
                            title="[tool]Tool Result: {0}[/tool]".format(
                                function_name),
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
                        error_msg = "[error]Error: Unknown function "
                        error_msg += "'{0}' requested by the LLM.".format(
                            function_name)
                        error_msg += "[/error]"
                        console.print(error_msg)
                        messages.append(
                            {
                                "tool_call_id": tool_call.get("id", ""),
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(
                                    {
                                        "error": "Function '{0}' ".format(
                                            function_name)
                                        + "not found by the client application."
                                    }
                                ),
                            }
                        )

                console.print(
                    Panel(
                        "[system]Sending tool response(s) back to LLM for next "
                        "step...[/system]",
                        border_style="bright_blue",
                    ))
                messages_for_api_tool_response = prune_messages(
                    list(messages), MAX_HISTORY_ITEMS
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn(
                        "[system]Waiting for LLM response after tool call..."
                        "[/system]"
                    ),
                    transient=True,
                ) as progress:
                    task = progress.add_task("waiting", total=None)
                    response_after_tool_obj = call_openrouter_api(
                        messages=messages_for_api_tool_response, model=LLM_MODEL
                    )

                has_valid_response = (
                    response_after_tool_obj
                    and "choices" in response_after_tool_obj
                    and len(response_after_tool_obj["choices"]) > 0
                )
                if not has_valid_response:
                    error_msg = "[error]Error: Invalid or empty response from "
                    error_msg += "API after sending tool results.[/error]"
                    console.print(error_msg)
                    resp_error = "[error]Response object: "
                    resp_error += "{0}[/error]".format(response_after_tool_obj)
                    console.print(resp_error)
                    tool_calls = None
                    response_message = None
                    break

                response_choice = response_after_tool_obj["choices"][0]
                if "message" not in response_choice:
                    error_msg = "[error]Error: API response's first choice "
                    error_msg += "(after tool call) has no message.[/error]"
                    console.print(error_msg)
                    resp_error = "[error]Response choice: "
                    resp_error += "{0}[/error]".format(response_choice)
                    console.print(resp_error)
                    tool_calls = None
                    break

                response_message = response_choice["message"]

                # Store response in messages list
                messages.append(response_message)

                # Check if there are more tool calls
                tool_calls = response_message.get("tool_calls", None)

            console.print("\n[assistant]Assistant:[/assistant]")
            has_content = (
                response_message
                and "content" in response_message
                and response_message["content"]
            )
            if has_content:
                # Check if the response contains markdown or code blocks
                if "```" in response_message["content"]:
                    # Process and render markdown with code blocks
                    md = Markdown(response_message["content"])
                    console.print(md)
                else:
                    # Regular text response
                    console.print(response_message["content"])
            else:
                warning_msg = "[warning](LLM provided no further text content "
                warning_msg += "for this turn, or an error occurred preventing "
                warning_msg += "a final message)[/warning]"
                console.print(warning_msg)

        except Exception as e:
            error_msg = "[error]An unexpected error occurred during "
            error_msg += "interaction: {0}[/error]".format(e)
            console.print(error_msg)
            traceback.print_exc()
            if messages and messages[-1]["role"] == "user":
                warning_msg = "[warning]--- Popping last user message due to "
                warning_msg += "API error to prevent re-submission. ---[/warning]"
                console.print(warning_msg)
                messages.pop()

        console.rule(style="bright_blue")

    console.print("\n[success]Script finished.[/success]")

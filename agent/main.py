#!/usr/bin/env python3
"""
File System Agent with AI Assistance

A CLI application that provides AI-assisted file operations and management.
"""

import argparse
import json
import os
import sys
import traceback
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure old and new tools directories are in the path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from agent.api import get_system_prompt, call_openrouter_api, prune_messages
from agent.commands import handle_special_command, get_welcome_message
from agent.console import console, display_logo, display_available_tools
from agent.conversation import load_messages_from_file
from agent.tools import get_tool_definitions, get_available_functions
from agent.tools.shared.path_utils import set_focus_path

# Constants
HISTORY_FILE = ".agent_history"


def main():
    """
    Main entry point for the application.
    """
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
    parser.add_argument(
        "--load",
        type=str,
        help="Load a previous conversation from the specified file.",
        default=None,
    )
    args = parser.parse_args()
    focus_path = args.path
    load_file = args.load

    # Display a fancy logo
    display_logo()

    # Check API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        error_msg = "[error]Error: OPENROUTER_API_KEY environment variable "
        error_msg += "is not set.[/error]"
        console.print(error_msg)
        exit(1)

    # Process and set the focus path if provided
    if focus_path:
        # Ensure the path is absolute for clarity in the prompt
        abs_focus_path = (
            os.path.abspath(focus_path)
            if not os.path.isabs(focus_path)
            else focus_path
        )
        if os.path.isdir(abs_focus_path):
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

    # Display welcome message
    console.print(
        Panel.fit(
            get_welcome_message(focus_path),
            title="🚀 Welcome",
            border_style="bright_blue",
        )
    )

    # Display available tools
    display_available_tools(get_tool_definitions())

    # Get system prompt
    system_content = get_system_prompt(focus_path)

    # Initialize messages list with system prompt
    messages = [{"role": "system", "content": system_content}]

    # Load a conversation if specified
    if load_file:
        result, loaded_messages = load_messages_from_file(load_file)
        if loaded_messages is not None:
            messages = loaded_messages
            console.print(
                Panel(
                    f"[success]Successfully loaded conversation from {load_file}[/success]",
                    border_style="bright_green",
                    title="🔄 Conversation Loaded"
                )
            )
        else:
            console.print(
                f"[error]Failed to load conversation from {load_file}. Starting with a new conversation.[/error]"
            )

    # Setup prompt_toolkit session with history
    session = PromptSession(history=FileHistory(HISTORY_FILE))

    # Main interaction loop
    while True:
        # Stylish user prompt
        try:
            # Use prompt_toolkit for input with history
            user_prompt = session.prompt("\nYou > ")
        except EOFError:
            # Handle Ctrl+D
            console.print("[success]Exiting chat session. Goodbye![/success]")
            break

        # Check for empty input
        if not user_prompt.strip():
            continue

        # Handle special commands
        cmd_result = handle_special_command(user_prompt, messages)
        if cmd_result is not None:
            # If the command was handled, either continue or exit based on the result
            if not cmd_result:
                break
            continue

        # Add user message to the conversation
        current_turn_messages = [{"role": "user", "content": user_prompt}]
        messages.append(current_turn_messages[0])

        # Prune messages for API call
        messages_for_api = prune_messages(list(messages), 10)  # Keep 10 recent messages

        try:
            # Process the user message and get response from OpenRouter
            # Show a spinner while waiting for the API response
            with Progress(
                SpinnerColumn(),
                TextColumn("[system]Assistant is thinking...[/system]"),
                transient=True,
            ) as progress:
                progress.add_task("thinking", total=None)

                response_obj = call_openrouter_api(
                    messages=messages_for_api,
                    tools=get_tool_definitions(),
                    tool_choice="auto",
                )

            # Validate the response
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

            # Process tool calls if any
            while tool_calls:
                console.print(
                    Panel(
                        "[tool]LLM wants to call a tool![/tool]",
                        border_style="bright_yellow",
                        expand=False,
                    )
                )

                # Get all available functions
                available_functions = get_available_functions(messages)

                # Process each tool call
                for tool_call in tool_calls:
                    function_data = tool_call.get("function", {})
                    function_name = function_data.get("name", "")
                    function_to_call = available_functions.get(function_name)

                    if function_to_call:
                        function_args_str = function_data.get("arguments", "{}")
                        # Display tool call information
                        display_tool_call(function_name, function_args_str)
                        
                        # Execute the tool call
                        tool_result = execute_tool_call(function_to_call, function_args_str)
                        
                        # Display tool results
                        display_tool_result(function_name, tool_result)

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
                        # Handle unknown function
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

                # Send tool response(s) back to LLM
                console.print(
                    Panel(
                        "[system]Sending tool response(s) back to LLM for next "
                        "step...[/system]",
                        border_style="bright_blue",
                    ))
                messages_for_api_tool_response = prune_messages(
                    list(messages), 10
                )

                # Wait for LLM response after tool call
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
                        messages=messages_for_api_tool_response
                    )

                # Validate the response after tool call
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

            # Display the assistant's response
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


def display_tool_call(function_name: str, function_args_str: str) -> None:
    """
    Display information about a tool call in a nice format.
    
    Args:
        function_name (str): The name of the function being called
        function_args_str (str): The arguments as a JSON string
    """
    from rich.table import Table
    table = Table(show_header=False, border_style="bright_yellow")
    table.add_column("", style="bright_yellow")
    table.add_column("", style="bright_white")
    table.add_row(
        "Function:", "[command]{0}[/command]".format(function_name)
    )

    # Format the JSON arguments nicely with syntax highlighting
    function_args_syntax = Syntax(
        function_args_str,
        "json",
        theme="monokai",
        line_numbers=False,
        word_wrap=True,
    )
    table.add_row("Arguments:", "")
    console.print(table)
    console.print(function_args_syntax)


def execute_tool_call(function_to_call, function_args_str: str) -> str:
    """
    Execute a tool call with the given function and arguments.
    
    Args:
        function_to_call: The function to call
        function_args_str (str): The arguments as a JSON string
        
    Returns:
        str: The result of the tool call as a JSON string
    """
    try:
        function_args = json.loads(function_args_str)
    except json.JSONDecodeError as e:
        error_msg = "[error]Error decoding JSON arguments: "
        error_msg += "{0}[/error]".format(e)
        console.print(error_msg)
        error_str = "[error]Problematic string: "
        error_str += "{0}[/error]".format(function_args_str)
        console.print(error_str)
        return json.dumps(
            {
                "error": "Invalid arguments format received from LLM."
            }
        )
    
    # Execute the function with the provided arguments
    with Progress(
        SpinnerColumn(),
        TextColumn(
            "[tool]Running {0}...[/tool]".format(
                function_to_call.__name__)
        ),
        transient=True,
    ) as progress:
        task = progress.add_task("running", total=None)
        tool_result = function_to_call(**function_args)

    # Ensure the result is a string
    if not isinstance(tool_result, str):
        warning_msg = "[warning]Warning: Tool "
        warning_msg += "'{0}' did not return ".format(
            function_to_call.__name__)
        warning_msg += "a string. Converting to JSON "
        warning_msg += "string.[/warning]"
        console.print(warning_msg)
        tool_result = json.dumps(
            {
                "output": tool_result,
                "warning": "Tool function did not return a string.",
            }
        )
        
    return tool_result


def display_tool_result(function_name: str, tool_result: str) -> None:
    """
    Display the result of a tool call in a nice format.
    
    Args:
        function_name (str): The name of the function that was called
        tool_result (str): The result of the tool call
    """
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


if __name__ == "__main__":
    main()

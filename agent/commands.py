"""
Command handling utilities.
Provides functionality to handle special commands entered by the user.
"""

from typing import List, Dict, Any, Optional, Union

from .console import console, display_help
from .conversation import dump_messages_to_file, load_messages_from_file


def handle_special_command(command: str, messages: List[Dict[str, Any]]) -> Optional[bool]:
    """
    Handle special commands typed by the user.
    
    Args:
        command (str): The command entered by the user
        messages (list): The current messages list
        
    Returns:
        bool or None: True if the command was handled and execution should continue, 
                     False if the agent should exit, None if not a special command
    """
    cmd_parts = command.strip().lower().split()
    base_cmd = cmd_parts[0] if cmd_parts else ""
    
    if base_cmd in ["exit", "quit"]:
        console.print("[success]Exiting chat session. Goodbye![/success]")
        return False
        
    elif base_cmd == "save" or base_cmd == "dump":
        # Extract filename if provided
        filename = cmd_parts[1] if len(cmd_parts) > 1 else None
        dump_messages_to_file(messages, filename)
        return True
        
    elif base_cmd == "load":
        if len(cmd_parts) < 2:
            console.print("[error]Please provide a filename to load[/error]")
        else:
            result, loaded_messages = load_messages_from_file(cmd_parts[1])
            if loaded_messages is not None:
                messages.clear()
                messages.extend(loaded_messages)
        return True
        
    elif base_cmd == "clear":
        # Keep only the system message
        if len(messages) > 0 and messages[0]["role"] == "system":
            system_msg = messages[0]
            messages.clear()
            messages.append(system_msg)
            console.print("[success]Conversation cleared.[/success]")
        else:
            messages.clear()
            console.print("[warning]Conversation cleared, including system message.[/warning]")
        return True
        
    elif base_cmd == "help":
        display_help()
        return True
        
    # If not a special command, continue with normal processing
    return None


def get_welcome_message(focus_path: Optional[str] = None) -> str:
    """
    Get the welcome message for the application.
    
    Args:
        focus_path (str, optional): The focus path for this session
        
    Returns:
        str: The welcome message
    """
    welcome_message = (
        "Starting interactive chat with OpenRouter assistant\n"
        "Type '[command]exit[/command]' or '[command]quit[/command]' to end the session\n"
        "Type '[command]save [filename][/command]' to save the conversation\n"
        "Type '[command]load <filename>[/command]' to load a previous conversation\n"
        "Type '[command]clear[/command]' to clear the conversation history\n"
        "Type '[command]help[/command]' to see all available commands\n"
        "File/directory paths for tools are relative to where this script is run"
    )
    
    if focus_path:
        info_msg = "\n[info]AI will focus on operations within or related to: "
        info_msg += f"{focus_path}[/info]"
        welcome_message += info_msg
        
    return welcome_message

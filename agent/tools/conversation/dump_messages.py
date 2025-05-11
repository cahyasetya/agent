import json
import os
import traceback
from datetime import datetime

from agent.tools.shared.path_utils import resolve_path


def dump_messages(filename: str = None, use_focus_path: bool = True):
    """
    Dumps the current conversation messages to a file for later continuation.
    This function is called by the main agent.py to save conversation state.
    
    Args:
        filename (str, optional): Name of the file to save messages to. 
                                  If not provided, uses a timestamped filename.
        use_focus_path (bool): Whether to use the focus path as base directory.
    
    Returns:
        str: A JSON string indicating success or error
    """
    # This is just the tool definition - actual implementation 
    # will be handled in agent.py since it needs access to messages
    return json.dumps({
        "error": "This function should be called directly by the agent, not through the LLM.",
        "status": "error"
    })


def load_messages(filename: str, use_focus_path: bool = True):
    """
    Loads conversation messages from a file to continue a previous conversation.
    This function is called by the main agent.py to load conversation state.
    
    Args:
        filename (str): Name of the file to load messages from.
        use_focus_path (bool): Whether to use the focus path as base directory.
    
    Returns:
        str: A JSON string indicating success or error
    """
    # This is just the tool definition - actual implementation 
    # will be handled in agent.py since it needs to modify messages
    return json.dumps({
        "error": "This function should be called directly by the agent, not through the LLM.",
        "status": "error"
    })


def get_tool_definition():
    return [
        {
            "type": "function",
            "function": {
                "name": "dump_messages",
                "description": "Saves the current conversation to a file so it can be continued later. "
                               "The conversation will be saved in JSON format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to save the conversation to. "
                                           "If not provided, a timestamped filename will be used. "
                                           "E.g., 'my_conversation.json'",
                        },
                        "use_focus_path": {
                            "type": "boolean",
                            "description": "Whether to use the focus path as the base directory. "
                                           "If true (default), the file will be saved relative to the focus directory "
                                           "if one is set. If false, it will be saved relative to the current working directory.",
                            "default": True,
                        }
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "load_messages",
                "description": "Loads a previously saved conversation from a file to continue where you left off.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The name of the file to load the conversation from. "
                                           "E.g., 'my_conversation.json'",
                        },
                        "use_focus_path": {
                            "type": "boolean",
                            "description": "Whether to use the focus path as the base directory. "
                                           "If true (default), the file will be loaded relative to the focus directory "
                                           "if one is set. If false, it will be loaded relative to the current working directory.",
                            "default": True,
                        }
                    },
                    "required": ["filename"],
                },
            },
        }
    ]

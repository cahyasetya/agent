"""
Conversation management utilities.
Provides functionality to save and load conversations to/from files.
"""

import json
import os
import traceback
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

from rich.panel import Panel

from .console import console
from .tools.shared.path_utils import resolve_path

# Directory for saving conversations
CONVERSATIONS_DIR = "conversations"

# Default model name
LLM_MODEL = "google/gemini-2.5-flash-preview"


def dump_messages_to_file(messages: List[Dict[str, Any]], 
                         filename: Optional[str] = None, 
                         use_focus_path: bool = True) -> str:
    """
    Dumps the current conversation messages to a file for later continuation.
    
    Args:
        messages (list): List of message objects to save
        filename (str, optional): Name of file to save to, or None for automatic naming
        use_focus_path (bool): Whether to use focus path for the file location
        
    Returns:
        str: JSON string with result information
    """
    try:
        # Create conversations directory if it doesn't exist
        conversations_path = CONVERSATIONS_DIR
        base_dir = os.getcwd()
        
        if use_focus_path:
            try:
                # Resolve path through our utility - handle the case where it returns a tuple
                result = resolve_path(conversations_path, use_focus_path)
                if isinstance(result, tuple) and len(result) >= 1:
                    resolved_path = result[0]
                    if len(result) >= 2:
                        base_dir = result[1]
                    conversations_path = resolved_path
                else:
                    # If it's not a tuple, assume it's the resolved path directly
                    conversations_path = result
            except Exception as e:
                print(f"Warning: Error resolving path: {e}")
                # Fall back to default path
                conversations_path = os.path.join(base_dir, CONVERSATIONS_DIR)
        
        os.makedirs(conversations_path, exist_ok=True)
        
        # Generate a filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        elif not filename.endswith('.json'):
            filename = f"{filename}.json"
            
        # Full path to the file
        file_path = os.path.join(conversations_path, filename)
        
        # Save the messages to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            # Include metadata in the dump
            data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": LLM_MODEL,
                },
                "messages": messages
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        console.print(
            Panel(
                f"[success]Conversation saved to: {file_path}[/success]",
                border_style="bright_green",
                title="💾 Save Successful"
            )
        )
        
        return json.dumps({
            "status": "success",
            "file_path": file_path,
            "message": f"Conversation successfully saved to {file_path}",
            "message_count": len(messages)
        })
        
    except Exception as e:
        error_msg = f"[error]Error saving conversation: {e}[/error]"
        console.print(error_msg)
        traceback.print_exc()
        
        return json.dumps({
            "status": "error",
            "error": str(e),
            "message": "Failed to save conversation"
        })


def load_messages_from_file(filename: str, 
                           use_focus_path: bool = True) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
    """
    Loads conversation messages from a file to continue a previous conversation.
    
    Args:
        filename (str): Name of the file to load from
        use_focus_path (bool): Whether to use focus path for the file location
        
    Returns:
        tuple: (JSON result string, loaded messages or None if failed)
    """
    try:
        # Handle conversations directory
        conversations_path = CONVERSATIONS_DIR
        base_dir = os.getcwd()
        
        if use_focus_path:
            try:
                # Resolve path through our utility - handle the case where it returns a tuple
                result = resolve_path(conversations_path, use_focus_path)
                if isinstance(result, tuple) and len(result) >= 1:
                    resolved_path = result[0]
                    if len(result) >= 2:
                        base_dir = result[1]
                    conversations_path = resolved_path
                else:
                    # If it's not a tuple, assume it's the resolved path directly
                    conversations_path = result
            except Exception as e:
                print(f"Warning: Error resolving path: {e}")
                # Fall back to default path
                conversations_path = os.path.join(base_dir, CONVERSATIONS_DIR)
        
        # Handle filename with or without extension
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
            
        # Full path to the file
        file_path = os.path.join(conversations_path, filename)
        
        if not os.path.exists(file_path):
            # Check for the file directly in the current directory as a fallback
            alt_path = os.path.join(base_dir, filename)
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                error_msg = f"[error]Conversation file not found: {file_path}[/error]"
                console.print(error_msg)
                return json.dumps({
                    "status": "error",
                    "error": "File not found",
                    "file_path": file_path,
                    "message": "Conversation file not found"
                }), None
        
        # Load the messages from the file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both formats: simple list of messages or structured data with metadata
        if isinstance(data, list):
            loaded_messages = data
            metadata = {"note": "No metadata available in this file format"}
        else:
            loaded_messages = data.get("messages", [])
            metadata = data.get("metadata", {"note": "No metadata available"})
            
        console.print(
            Panel(
                f"[success]Conversation loaded from: {file_path}[/success]\n"
                f"[info]Message count: {len(loaded_messages)}[/info]\n"
                f"[info]Model: {metadata.get('model', 'Unknown')}[/info]",
                border_style="bright_green",
                title="📂 Load Successful"
            )
        )
        
        return json.dumps({
            "status": "success",
            "file_path": file_path,
            "message": f"Conversation successfully loaded from {file_path}",
            "message_count": len(loaded_messages),
            "metadata": metadata
        }), loaded_messages
        
    except Exception as e:
        error_msg = f"[error]Error loading conversation: {e}[/error]"
        console.print(error_msg)
        traceback.print_exc()
        
        return json.dumps({
            "status": "error",
            "error": str(e),
            "message": "Failed to load conversation"
        }), None

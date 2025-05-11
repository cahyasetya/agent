import json
import os
import traceback

from tools.shared.path_utils import resolve_path
from tools.shared.gitignore_parser import parse_gitignore, is_ignored


def list_directory_contents(directory_path: str = ".", use_focus_path: bool = True, respect_gitignore: bool = True):
    """
    Lists the contents (files and subdirectories) of a specified directory.
    
    Args:
        directory_path (str): The path to the directory to list (relative to base directory).
        use_focus_path (bool): Whether to use the focus path as base directory.
        respect_gitignore (bool): Whether to respect .gitignore patterns and filter out ignored files.
        
    Returns:
        str: A JSON string representing the directory contents or an error.
    """
    print(
        f"--- TOOL EXECUTING: list_directory_contents(directory_path='{directory_path}', "
        f"use_focus_path={use_focus_path}, respect_gitignore={respect_gitignore}) ---"
    )
    try:
        if not isinstance(directory_path, str):
            return json.dumps(
                {
                    "error": "Invalid directory_path type, must be a string.",
                    "path_received": str(directory_path),
                    "status": "error",
                }
            )

        # Resolve the path using the shared utility
        resolved_path, base_dir, is_in_base_dir = resolve_path(directory_path, use_focus_path)

        if not is_in_base_dir:
            print(
                f"Security Alert: Attempt to access path '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: Path is outside the allowed directory.",
                    "path": directory_path,
                    "base_directory": base_dir,
                    "status": "error",
                }
            )

        if not os.path.exists(resolved_path):
            return json.dumps(
                {
                    "error": "Directory not found.", 
                    "path": directory_path,
                    "resolved_path": resolved_path,
                    "status": "error",
                }
            )
        if not os.path.isdir(resolved_path):
            return json.dumps(
                {
                    "error": "The specified path is not a directory.",
                    "path": resolved_path,
                    "status": "error",
                }
            )

        # Get gitignore patterns if needed
        patterns = []
        if respect_gitignore:
            patterns = parse_gitignore(base_dir)
            print(f"Using gitignore patterns: {patterns}")

        contents = os.listdir(resolved_path)
        detailed_contents = []
        ignored_count = 0
        
        for item in contents:
            item_path = os.path.join(resolved_path, item)
            rel_path = os.path.join(directory_path, item)
            
            # Determine if item should be ignored
            should_ignore = False
            if respect_gitignore:
                should_ignore = is_ignored(item_path, patterns)
                
                # Handle common directories that should always be ignored
                if item in ["venv", ".git", "__pycache__", "node_modules"]:
                    should_ignore = True
                
            if should_ignore:
                ignored_count += 1
                print(f"Ignoring: {item_path}")
                continue
                
            item_type = "directory" if os.path.isdir(item_path) else "file"
            detailed_contents.append({"name": item, "type": item_type})

        if not detailed_contents:
            message = "The directory is empty."
            if ignored_count > 0:
                message = f"The directory has {ignored_count} item(s), but all are ignored by gitignore patterns."
                
            return json.dumps(
                {
                    "path": directory_path,
                    "resolved_path": resolved_path,
                    "contents": [],
                    "ignored_count": ignored_count,
                    "message": message,
                    "status": "success",
                }
            )

        return json.dumps(
            {
                "path": directory_path,
                "resolved_path": resolved_path,
                "contents": detailed_contents,
                "ignored_count": ignored_count,
                "status": "success",
            }
        )

    except Exception as e:
        print(f"Error in list_directory_contents: {e}")
        traceback.print_exc()
        return json.dumps(
            {
                "error": str(e), 
                "path": directory_path,
                "status": "error",
            }
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "list_directory_contents",
            "description": "Lists the files and subdirectories within a specified directory path. Paths are relative to the current working directory or focus directory if one is set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "The path to the directory to inspect. e.g., '.', 'example_dir'",
                    },
                    "use_focus_path": {
                        "type": "boolean",
                        "description": "Whether to use the focus path as the base directory. "
                        "If true (default), paths are relative to the focus directory if one is set. "
                        "If false, paths are always relative to the current working directory.",
                        "default": True,
                    },
                    "respect_gitignore": {
                        "type": "boolean",
                        "description": "Whether to respect .gitignore patterns and filter out ignored files. "
                        "If true (default), ignores files matching patterns in .gitignore. "
                        "If false, lists all files in the directory.",
                        "default": True,
                    }
                },
                "required": ["directory_path"],
            },
        },
    }

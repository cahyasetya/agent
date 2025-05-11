import json
import os
import traceback


def create_directory(directory_path: str):
    """
    Creates a directory at the specified path.
    Parent directories will also be created if they don't exist.
    Args:
        directory_path (str): The path for the new directory (relative to script's CWD).
    Returns:
        str: A JSON string indicating success or an error message.
    """
    print(
        f"--- TOOL EXECUTING: create_directory(directory_path='{directory_path}') ---"
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

        base_dir = os.getcwd()
        resolved_path = os.path.abspath(os.path.join(base_dir, directory_path))

        if not resolved_path.startswith(base_dir):
            print(
                f"Security Alert: Attempt to create directory '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: Directory path is outside the allowed directory.",
                    "directory_path": directory_path,
                    "status": "error",
                })

        if os.path.exists(resolved_path) and os.path.isdir(resolved_path):
            return json.dumps(
                {
                    "directory_path": directory_path,
                    "status": "exists",
                    "message": f"Directory '{resolved_path}' already exists.",
                }
            )
        elif os.path.exists(resolved_path) and not os.path.isdir(resolved_path):
            return json.dumps(
                {
                    "directory_path": directory_path,
                    "status": "error",
                    "message": f"Error: A file with the name '{resolved_path}' already exists.",
                })

        os.makedirs(resolved_path, exist_ok=True)
        return json.dumps(
            {
                "directory_path": directory_path,
                "status": "created",
                "message": f"Directory '{resolved_path}' created successfully or already existed.",
            })

    except Exception as e:
        print(f"Error in create_directory: {e}")
        traceback.print_exc()
        return json.dumps(
            {
                "error": str(e),
                "directory_path": directory_path,
                "status": "error",
            }
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Creates a new directory at the specified path. Parent directories will also be created if they do not exist. Paths are relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "The relative path for the new directory. e.g., 'new_folder' or 'data/archive'",
                    }},
                "required": ["directory_path"],
            },
        },
    }

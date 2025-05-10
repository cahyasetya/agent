import json
import os
import traceback


def list_directory_contents(directory_path: str = "."):
    """
    Lists the contents (files and subdirectories) of a specified directory.
    Args:
        directory_path (str): The path to the directory to list.
    Returns:
        str: A JSON string representing the directory contents or an error.
    """
    print(
        f"--- TOOL EXECUTING: list_directory_contents(directory_path='{directory_path}') ---"
    )
    try:
        if not isinstance(directory_path, str):
            return json.dumps(
                {
                    "error": "Invalid directory_path type, must be a string.",
                    "path_received": str(directory_path),
                }
            )

        base_dir = os.getcwd()
        resolved_path = os.path.abspath(os.path.join(base_dir, directory_path))

        if not resolved_path.startswith(base_dir):
            print(
                f"Security Alert: Attempt to access path '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: Path is outside the allowed directory.",
                    "path": directory_path,
                }
            )

        if not os.path.exists(resolved_path):
            return json.dumps({"error": "Directory not found.", "path": resolved_path})
        if not os.path.isdir(resolved_path):
            return json.dumps(
                {
                    "error": "The specified path is not a directory.",
                    "path": resolved_path,
                }
            )

        contents = os.listdir(resolved_path)
        detailed_contents = []
        for item in contents:
            item_path = os.path.join(resolved_path, item)
            item_type = "directory" if os.path.isdir(item_path) else "file"
            detailed_contents.append({"name": item, "type": item_type})

        if not detailed_contents:
            return json.dumps(
                {
                    "path": directory_path,
                    "contents": [],
                    "message": "The directory is empty.",
                }
            )

        return json.dumps({"path": directory_path, "contents": detailed_contents})

    except Exception as e:
        print(f"Error in list_directory_contents: {e}")
        traceback.print_exc()
        return json.dumps({"error": str(e), "path": directory_path})


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "list_directory_contents",
            "description": "Lists the files and subdirectories within a specified directory path. Paths are relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "The path to the directory to inspect. e.g., '.', 'example_dir'",
                    }
                },
                "required": ["directory_path"],
            },
        },
    }

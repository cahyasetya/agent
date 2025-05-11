import json
import os
import shutil
import traceback


def delete_directory(directory_path: str):
    """
    Deletes a specified directory and all its contents.
    Args:
        directory_path (str): The path to the directory to delete (relative to the script's CWD).
    Returns:
        str: A JSON string indicating success or an error message.
    """
    print(
        f"--- TOOL EXECUTING: delete_directory(directory_path='{directory_path}') ---"
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
                f"Security Alert: Attempt to delete directory '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: Directory path is outside the allowed directory.",
                    "directory_path": directory_path,
                    "status": "error",
                })

        if not os.path.exists(resolved_path):
            return json.dumps(
                {
                    "directory_path": directory_path,
                    "status": "not_found",
                    "message": f"Directory '{resolved_path}' not found.",
                }
            )
        if not os.path.isdir(resolved_path):
            return json.dumps(
                {
                    "directory_path": directory_path,
                    "status": "error",
                    "message": f"Path '{resolved_path}' is not a directory.",
                }
            )

        # Prevent accidental deletion of the root directory
        if resolved_path == base_dir:
            return json.dumps(
                {
                    "directory_path": directory_path,
                    "status": "error",
                    "message": "Cannot delete the current working directory.",
                }
            )

        shutil.rmtree(resolved_path)
        return json.dumps(
            {
                "directory_path": directory_path,
                "status": "success",
                "message": f"Directory '{resolved_path}' and its contents deleted successfully.",
            })

    except Exception as e:
        print(f"Error in delete_directory: {e}")
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
            "name": "delete_directory",
            "description": "Deletes a specified directory and all its contents. Paths are relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {
                        "type": "string",
                        "description": "The relative path to the directory to delete. e.g., 'old_folder' or 'temp_data'",
                    }},
                "required": ["directory_path"],
            },
        },
    }

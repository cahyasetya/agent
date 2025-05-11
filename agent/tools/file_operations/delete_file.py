import json
import os
import traceback


def delete_file(file_path: str):
    """
    Deletes a specified file.
    Args:
        file_path (str): The path to the file to delete (relative to the script's CWD).
    Returns:
        str: A JSON string indicating success or an error message.
    """
    print(f"--- TOOL EXECUTING: delete_file(file_path='{file_path}') ---")
    try:
        if not isinstance(file_path, str):
            return json.dumps(
                {
                    "error": "Invalid file_path type, must be a string.",
                    "path_received": str(file_path),
                    "status": "error",
                }
            )

        base_dir = os.getcwd()
        resolved_path = os.path.abspath(os.path.join(base_dir, file_path))

        if not resolved_path.startswith(base_dir):
            print(
                f"Security Alert: Attempt to delete file '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: File path is outside the allowed directory.",
                    "file_path": file_path,
                    "status": "error",
                })

        if not os.path.exists(resolved_path):
            return json.dumps(
                {
                    "file_path": file_path,
                    "status": "not_found",
                    "message": f"File '{resolved_path}' not found.",
                }
            )
        if not os.path.isfile(resolved_path):
            return json.dumps(
                {
                    "file_path": file_path,
                    "status": "error",
                    "message": f"Path '{resolved_path}' is not a file.",
                }
            )

        os.remove(resolved_path)
        return json.dumps(
            {
                "file_path": file_path,
                "status": "success",
                "message": f"File '{resolved_path}' deleted successfully.",
            }
        )

    except Exception as e:
        print(f"Error in delete_file: {e}")
        traceback.print_exc()
        return json.dumps(
            {"error": str(e), "file_path": file_path, "status": "error"}
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Deletes a specified file. File paths are relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file to delete. e.g., 'old_document.txt' or 'temp/data.bak'",
                    }},
                "required": ["file_path"],
            },
        },
    }

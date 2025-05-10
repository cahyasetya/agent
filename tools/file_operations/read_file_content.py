import json
import os
import traceback


def read_file_content(file_path: str):
    """
    Reads the content of a specified file.
    Args:
        file_path (str): The path to the file to read (relative to the script's CWD).
    Returns:
        str: A JSON string containing the file content or an error message.
    """
    print(f"--- TOOL EXECUTING: read_file_content(file_path='{file_path}') ---")
    MAX_FILE_SIZE_WARN = 1024 * 1024  # 1MB, for console warning
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
                f"Security Alert: Attempt to read file '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: File path is outside the allowed directory.",
                    "file_path": file_path,
                    "status": "error",
                }
            )

        if not os.path.exists(resolved_path):
            return json.dumps(
                {"error": "File not found.", "file_path": file_path, "status": "error"}
            )
        if not os.path.isfile(resolved_path):
            return json.dumps(
                {
                    "error": "The specified path is not a file.",
                    "file_path": resolved_path,
                    "status": "error",
                }
            )

        file_size = os.path.getsize(resolved_path)
        if file_size > MAX_FILE_SIZE_WARN:
            print(
                f"Warning: File '{resolved_path}' is large ({file_size / (1024):.2f} KB). Reading entire content."
            )

        with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content_to_return = content  # No truncation

        return json.dumps(
            {"file_path": file_path, "content": content_to_return, "status": "success"}
        )

    except FileNotFoundError:
        return json.dumps(
            {
                "error": "File not found during read operation.",
                "file_path": file_path,
                "status": "error",
            }
        )
    except Exception as e:
        print(f"Error in read_file_content: {e}")
        traceback.print_exc()
        return json.dumps({"error": str(e), "file_path": file_path, "status": "error"})


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Reads and returns the content of a specified text file. File paths are relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file to be read. e.g., 'document.txt' or 'folder/data.csv'",
                    }
                },
                "required": ["file_path"],
            },
        },
    }

import json
import os
import traceback

from tools.shared.path_utils import resolve_path


def write_to_file(file_path: str, content: str, use_focus_path: bool = True):
    """
    Writes the given content to a specified file, optionally using the focus path.
    If the file exists, it will be overwritten. If it doesn't exist, it will be created.
    
    Args:
        file_path (str): The path to the file to write (relative to base directory).
        content (str): The content to write to the file.
        use_focus_path (bool): Whether to use the focus path as base directory.
        
    Returns:
        str: A JSON string indicating success or an error message.
    """
    print(
        f"--- TOOL EXECUTING: write_to_file(file_path='{file_path}', content_length={len(content)}, use_focus_path={use_focus_path}) ---"
    )
    try:
        if not isinstance(file_path, str):
            return json.dumps(
                {
                    "error": "Invalid file_path type, must be a string.",
                    "path_received": str(file_path),
                    "status": "error",
                }
            )
        if not isinstance(content, str):
            return json.dumps(
                {
                    "error": "Invalid content type, must be a string.",
                    "file_path": file_path,
                    "status": "error",
                }
            )

        # Resolve the path using the shared utility
        resolved_path, base_dir, is_in_base_dir = resolve_path(file_path, use_focus_path)

        if not is_in_base_dir:
            print(
                f"Security Alert: Attempt to write file '{resolved_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: File path is outside the allowed directory.",
                    "file_path": file_path,
                    "base_directory": base_dir,
                    "status": "error",
                })

        parent_dir = os.path.dirname(resolved_path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
                print(f"Created parent directory: {parent_dir}")
            except Exception as e_mkdir:
                print(
                    f"Error creating parent directory {parent_dir}: {e_mkdir}"
                )
                return json.dumps(
                    {
                        "error": f"Could not create parent directory: {str(e_mkdir)}",
                        "file_path": file_path,
                        "status": "error",
                    })

        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(content)

        return json.dumps(
            {
                "file_path": file_path,
                "resolved_path": resolved_path,
                "status": "success",
                "message": f"Content successfully written to {resolved_path}.",
            }
        )

    except Exception as e:
        print(f"Error in write_to_file: {e}")
        traceback.print_exc()
        return json.dumps(
            {"error": str(e), "file_path": file_path, "status": "error"}
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Writes the given string content to a specified file. If the file exists, it will be overwritten. If it does not exist, it will be created. File paths are relative to the current working directory or focus directory if one is set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file where content will be written. e.g., 'output.txt' or 'folder/notes.md'",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file.",
                    },
                    "use_focus_path": {
                        "type": "boolean",
                        "description": "Whether to use the focus path as the base directory. "
                        "If true (default), paths are relative to the focus directory if one is set. "
                        "If false, paths are always relative to the current working directory.",
                        "default": True,
                    }
                },
                "required": [
                    "file_path",
                    "content"],
            },
        },
    }

import json
import os
import traceback

from tools.shared.path_utils import resolve_path


def read_file_content(file_path: str, use_focus_path: bool = True):
    """
    Reads the content of a specified file, optionally using the focus path.
    
    Args:
        file_path (str): The path to the file to read (relative to base directory).
        use_focus_path (bool): Whether to use the focus path as base directory.
        
    Returns:
        str: A JSON string containing the file content or an error message.
    """
    print(f"--- TOOL EXECUTING: read_file_content(file_path='{file_path}', use_focus_path={use_focus_path}) ---")
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

        # Resolve the path using the shared utility
        resolved_path, base_dir, is_in_base_dir = resolve_path(file_path, use_focus_path)

        if not is_in_base_dir:
            alert_msg = "Security Alert: Attempt to read file "
            alert_msg += f"'{resolved_path}' outside of base directory '{base_dir}'."
            print(alert_msg)
            return json.dumps(
                {
                    "error": "Access denied: File path is outside the allowed directory.",
                    "file_path": file_path,
                    "base_directory": base_dir,
                    "status": "error",
                })

        if not os.path.exists(resolved_path):
            return json.dumps(
                {
                    "error": "File not found.",
                    "file_path": file_path,
                    "resolved_path": resolved_path,
                    "status": "error",
                }
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
            warn_msg = f"Warning: File '{resolved_path}' is large "
            warn_msg += f"({file_size / (1024):.2f} KB). Reading entire content."
            print(warn_msg)

        with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content_to_return = content  # No truncation

        return json.dumps(
            {
                "file_path": file_path,
                "resolved_path": resolved_path,
                "content": content_to_return,
                "status": "success",
            }
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
        return json.dumps(
            {"error": str(e), "file_path": file_path, "status": "error"}
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Reads and returns the content of a specified text file. "
            "File paths are relative to the current working directory or focus directory if one is set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file to be read. "
                        "e.g., 'document.txt' or 'folder/data.csv'",
                    },
                    "use_focus_path": {
                        "type": "boolean",
                        "description": "Whether to use the focus path as the base directory. "
                        "If true (default), paths are relative to the focus directory if one is set. "
                        "If false, paths are always relative to the current working directory.",
                        "default": True,
                    }
                },
                "required": ["file_path"],
            },
        },
    }

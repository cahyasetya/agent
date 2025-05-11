import json
import os

from tools.shared.path_utils import resolve_path


def get_tool_definition():
    """
    Define the create_empty_file tool for the OpenAI function calling API.
    """
    return {
        "type": "function",
        "function": {
            "name": "create_empty_file",
            "description": "Create a new empty file at the specified path. File paths are relative to the current working directory or focus directory if one is set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path where the new file should be created. Relative to the current directory or focus directory if one is set.",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Whether to overwrite an existing file with the same name. Defaults to False.",
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


def create_empty_file(file_path, overwrite=False, use_focus_path=True):
    """
    Create a new empty file at the specified path.

    Args:
        file_path (str): Path to create the new file
        overwrite (bool, optional): Whether to overwrite if file exists. Defaults to False.
        use_focus_path (bool, optional): Whether to use the focus path as base directory. Defaults to True.

    Returns:
        str: JSON string containing result status and info.
    """
    print(f"--- TOOL EXECUTING: create_empty_file(file_path='{file_path}', overwrite={overwrite}, use_focus_path={use_focus_path}) ---")
    
    try:
        # Resolve the path using the shared utility
        resolved_path, base_dir, is_in_base_dir = resolve_path(file_path, use_focus_path)

        if not is_in_base_dir:
            alert_msg = "Security Alert: Attempt to create file "
            alert_msg += f"'{resolved_path}' outside of base directory '{base_dir}'."
            print(alert_msg)
            return json.dumps(
                {
                    "error": "Access denied: File path is outside the allowed directory.",
                    "file_path": file_path,
                    "base_directory": base_dir,
                    "status": "error",
                })

        # Check if file exists and handle accordingly
        if os.path.exists(resolved_path):
            if not overwrite:
                return json.dumps(
                    {
                        "error": f"File already exists at '{resolved_path}' and overwrite is False.",
                        "status": "error"
                    }
                )

            # If overwrite is True, we'll go ahead and create/overwrite the file

        # Ensure directory exists
        dir_name = os.path.dirname(resolved_path)
        if dir_name and not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name)
                print(f"Created parent directory: {dir_name}")
            except OSError as e:
                return json.dumps(
                    {
                        "error": f"Could not create directory '{dir_name}': {str(e)}",
                        "status": "error"
                    }
                )

        # Create the empty file
        with open(
            resolved_path, "w"
        ) as _:  # Using _ to indicate we don't need the file object
            pass

        return json.dumps(
            {
                "file_path": file_path,
                "resolved_path": resolved_path,
                "status": "success",
                "message": f"Empty file created at '{resolved_path}'",
            }
        )

    except Exception as e:
        return json.dumps(
            {
                "error": f"An error occurred creating empty file: {str(e)}",
                "file_path": file_path,
                "status": "error"
            }
        )

import json
import os


def get_tool_definition():
    """
    Define the create_empty_file tool for the OpenAI function calling API.
    """
    return {
        "type": "function",
        "function": {
            "name": "create_empty_file",
            "description": "Create a new empty file at the specified path",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path (absolute or relative) where the new file should be created",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Whether to overwrite an existing file with the same name. Defaults to False.",
                    },
                },
                "required": ["file_path"],
            },
        },
    }


def create_empty_file(file_path, overwrite=False):
    """
    Create a new empty file at the specified path.

    Args:
        file_path (str): Path to create the new file
        overwrite (bool, optional): Whether to overwrite if file exists. Defaults to False.

    Returns:
        str: JSON string containing result status and info.
    """
    try:
        # Convert to absolute path if needed for clarity in response
        abs_path = os.path.abspath(file_path)

        # Check if file exists and handle accordingly
        if os.path.exists(abs_path):
            if not overwrite:
                return json.dumps(
                    {
                        "error": f"File already exists at '{abs_path}' and overwrite is False."
                    }
                )

            # If overwrite is True, we'll go ahead and create/overwrite the file

        # Ensure directory exists
        dir_name = os.path.dirname(abs_path)
        if dir_name and not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name)
            except OSError as e:
                return json.dumps(
                    {"error": f"Could not create directory '{dir_name}': {str(e)}"}
                )

        # Create the empty file
        with open(
            abs_path, "w"
        ) as _:  # Using _ to indicate we don't need the file object
            pass

        return json.dumps(
            {
                "success": True,
                "file_path": abs_path,
                "message": f"Empty file created at '{abs_path}'",
            }
        )

    except Exception as e:
        return json.dumps({"error": f"An error occurred creating empty file: {str(e)}"})

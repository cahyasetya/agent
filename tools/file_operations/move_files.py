import glob
import json
import os
import shutil


def get_tool_definition():
    """
    Define the move_files tool for the OpenAI function calling API.
    """
    return {
        "type": "function",
        "function": {
            "name": "move_files",
            "description": "Move files or folders from source path to destination, supporting wildcards",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Source path with optional wildcard (*, ?, [seq], [!seq]) patterns",
                    },
                    "destination_path": {
                        "type": "string",
                        "description": "Destination path (directory for wildcards, specific path for single file)",
                    },
                    "overwrite": {
                        "type": "boolean",
                        "description": "Whether to overwrite files at destination if they exist. Default is False.",
                        "default": False,
                    },
                },
                "required": ["source_path", "destination_path"],
            },
        },
    }


def move_files(source_path, destination_path, overwrite=False):
    """
    Move files or folders from source path to destination, supporting wildcards.

    Args:
        source_path (str): Source path with optional wildcard patterns
        destination_path (str): Destination path (directory for wildcards, specific path for single file)
        overwrite (bool): Whether to overwrite files at destination if they exist. Default is False.

    Returns:
        str: JSON string containing result status and info.
    """
    try:
        # Convert to absolute paths for clarity in response
        abs_source_path = os.path.abspath(source_path)
        abs_destination_path = os.path.abspath(destination_path)

        # Check if source_path has wildcards
        has_wildcards = any(c in source_path for c in ["*", "?", "[", "]"])

        if has_wildcards:
            # Handle wildcard pattern in source path
            matched_paths = glob.glob(abs_source_path, recursive=True)

            if not matched_paths:
                return json.dumps(
                    {
                        "warning": True,
                        "message": f"No files found matching pattern '{abs_source_path}'.",
                    }
                )

            # Destination must be a directory for multiple files
            if len(matched_paths) > 1 and not os.path.isdir(abs_destination_path):
                # Create destination directory if it doesn't exist
                try:
                    os.makedirs(abs_destination_path, exist_ok=True)
                except Exception as e:
                    return json.dumps(
                        {
                            "error": f"Cannot create destination directory '{abs_destination_path}': {str(e)}"
                        }
                    )

            # Process each matched item
            results = []
            for item_path in matched_paths:
                item_name = os.path.basename(item_path)
                # For multiple files, determine the destination for each file
                if os.path.isdir(abs_destination_path):
                    item_destination = os.path.join(abs_destination_path, item_name)
                else:
                    item_destination = abs_destination_path

                # Check if destination exists and handle accordingly
                if os.path.exists(item_destination):
                    if not overwrite:
                        results.append(
                            {
                                "source": item_path,
                                "destination": item_destination,
                                "status": "skipped",
                                "message": "Destination exists and overwrite is False.",
                            }
                        )
                        continue

                    # If overwrite is True but destination is a directory and source is a file (or vice versa),
                    # we cannot overwrite without removing first
                    if os.path.isdir(item_destination) != os.path.isdir(item_path):
                        results.append(
                            {
                                "source": item_path,
                                "destination": item_destination,
                                "status": "error",
                                "message": "Cannot overwrite: source and destination are different types (file/directory).",
                            }
                        )
                        continue

                # Move the item
                try:
                    # For directories, we use shutil.move
                    # For files, we use shutil.move as well
                    shutil.move(item_path, item_destination)

                    results.append(
                        {
                            "source": item_path,
                            "destination": item_destination,
                            "status": "success",
                            "message": f"{'Directory' if os.path.isdir(item_path) else 'File'} moved successfully.",
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "source": item_path,
                            "destination": item_destination,
                            "status": "error",
                            "message": f"Error moving: {str(e)}",
                        }
                    )

            return json.dumps(
                {
                    "results": results,
                    "total": len(matched_paths),
                    "success": sum(1 for r in results if r["status"] == "success"),
                    "errors": sum(1 for r in results if r["status"] == "error"),
                    "skipped": sum(1 for r in results if r["status"] == "skipped"),
                }
            )

        else:
            # Single file or directory move (no wildcards)
            if not os.path.exists(abs_source_path):
                return json.dumps(
                    {"error": f"Source path '{abs_source_path}' does not exist."}
                )

            # Check if destination exists and handle accordingly
            if os.path.exists(abs_destination_path):
                if not overwrite:
                    return json.dumps(
                        {
                            "warning": True,
                            "message": f"Destination '{abs_destination_path}' already exists and overwrite is False.",
                        }
                    )

                # If overwrite is True but destination is a directory and source is a file (or vice versa),
                # we cannot overwrite without removing first
                if os.path.isdir(abs_destination_path) != os.path.isdir(
                    abs_source_path
                ):
                    return json.dumps(
                        {
                            "error": "Cannot overwrite: source and destination are different types (file/directory)."
                        }
                    )

            # Make sure parent directory of destination exists
            parent_dir = os.path.dirname(abs_destination_path)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except Exception as e:
                    return json.dumps(
                        {
                            "error": f"Cannot create parent directory for destination: {str(e)}"
                        }
                    )

            # Move the item
            try:
                shutil.move(abs_source_path, abs_destination_path)
                return json.dumps(
                    {
                        "success": True,
                        "message": f"{'Directory' if os.path.isdir(abs_source_path) else 'File'} moved from '{abs_source_path}' to '{abs_destination_path}'.",
                    }
                )
            except Exception as e:
                return json.dumps({"error": f"Error moving file/directory: {str(e)}"})

    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

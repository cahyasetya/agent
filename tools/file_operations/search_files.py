import fnmatch
import json
import os
import traceback
from tools.shared.gitignore_parser import parse_gitignore, is_ignored


def search_files(search_path: str = ".", file_pattern: str = "*", respect_gitignore: bool = True):
    """
    Searches for files matching a pattern within a directory and its subdirectories.
    Args:
        search_path (str): The directory to start searching from (relative to CWD). Defaults to current directory.
        file_pattern (str): The file pattern to match (e.g., '*.txt', 'data_*.csv'). Defaults to '*'.
        respect_gitignore (bool): Whether to respect .gitignore patterns. Defaults to True.
    Returns:
        str: A JSON string with a list of found files or an error message.
    """
    print(
        f"--- TOOL EXECUTING: search_files(search_path='{search_path}', file_pattern='{file_pattern}', respect_gitignore={respect_gitignore}) ---"
    )
    try:
        if not isinstance(search_path, str):
            return json.dumps(
                {
                    "error": "Invalid search_path type, must be a string.",
                    "path_received": str(search_path),
                    "status": "error",
                }
            )
        if not isinstance(file_pattern, str):
            return json.dumps(
                {
                    "error": "Invalid file_pattern type, must be a string.",
                    "pattern_received": str(file_pattern),
                    "status": "error",
                }
            )

        base_dir = os.getcwd()
        resolved_search_path = os.path.abspath(
            os.path.join(base_dir, search_path)
        )

        if not resolved_search_path.startswith(base_dir):
            print(
                f"Security Alert: Attempt to search in '{resolved_search_path}' outside of base directory '{base_dir}'."
            )
            return json.dumps(
                {
                    "error": "Access denied: Search path is outside the allowed directory.",
                    "search_path": search_path,
                    "status": "error",
                })

        if not os.path.isdir(resolved_search_path):
            return json.dumps(
                {
                    "error": "Search path is not a valid directory.",
                    "search_path": resolved_search_path,
                    "status": "error",
                }
            )

        found_files = []
        gitignore_patterns = []
        if respect_gitignore:
            gitignore_patterns = parse_gitignore(base_dir)

        for root, dirs, files in os.walk(resolved_search_path):
            # Filter out ignored directories first
            if respect_gitignore:
                 dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), gitignore_patterns)]

            for filename in files:
                full_path = os.path.join(root, filename)
                # Convert to relative path for gitignore check
                relative_path = os.path.relpath(full_path, base_dir)

                if respect_gitignore and is_ignored(relative_path, gitignore_patterns):
                    continue

                if fnmatch.fnmatch(filename, file_pattern):
                    relative_file_path_from_search = os.path.relpath(
                        full_path, resolved_search_path
                    )
                    found_files.append(
                        os.path.join(search_path, relative_file_path_from_search).replace(
                            "\\", "/"
                        )
                    )

        if not found_files:
            return json.dumps(
                {
                    "search_path": search_path,
                    "file_pattern": file_pattern,
                    "found_files": [],
                    "message": "No files found matching the pattern.",
                }
            )

        return json.dumps(
            {
                "search_path": search_path,
                "file_pattern": file_pattern,
                "found_files": found_files,
                "status": "success",
            }
        )

    except Exception as e:
        print(f"Error in search_files: {e}")
        traceback.print_exc()
        return json.dumps(
            {
                "error": str(e),
                "search_path": search_path,
                "file_pattern": file_pattern,
                "status": "error",
            }
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Searches for files matching a specific pattern within a given directory and its subdirectories. Paths are relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_path": {
                        "type": "string",
                        "description": "The directory path to start the search from. Defaults to the current working directory ('.') if not specified.",
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "The file pattern to search for (e.g., '*.txt', 'report_*.docx', '*'). Defaults to '*' (all files) if not specified.",
                    },
                    "respect_gitignore": {
                         "type": "boolean",
                         "description": "Whether to respect .gitignore patterns and filter out ignored files and directories. If true (default), ignores files matching patterns in .gitignore. If false, lists all files in the directory.",
                    },
                },
                "required": [],
            }
        },
    }

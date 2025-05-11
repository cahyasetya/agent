import difflib
import json
import os
import traceback

import colorama
from agent.tools.shared.path_utils import resolve_path

# Initialize colorama for colored output in the terminal
colorama.init()


class TermColors:
    """Terminal colors for diff output."""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    # Using bold red and green for clearer distinction
    BOLD_RED = "\033[1;91m"
    BOLD_GREEN = "\033[1;92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def get_diff_for_proposed_changes(file_path: str, proposed_new_content: str, use_focus_path: bool = True):
    """
    Calculates and returns a colored diff between a file's current content and
    proposed new content.
    
    Args:
        file_path (str): The path to the file (relative to base directory).
        proposed_new_content (str): The full proposed new content for the file.
        use_focus_path (bool): Whether to use the focus path as base directory.
        
    Returns:
        str: A JSON string containing the colored diff or an error message.
    """
    log_msg = "--- TOOL EXECUTING: get_diff_for_proposed_changes"
    log_msg += "(file_path='{}', ".format(file_path)
    log_msg += "proposed_content_length={}, ".format(len(proposed_new_content))
    log_msg += "use_focus_path={}) ---".format(use_focus_path)
    print(log_msg)

    try:
        # Resolve the path using the shared utility
        resolved_path, base_dir, is_in_base_dir = resolve_path(file_path, use_focus_path)

        if not is_in_base_dir:
            alert_msg = "Security Alert: Attempt to access file "
            alert_msg += f"'{resolved_path}' outside of base directory '{base_dir}'."
            print(alert_msg)
            return json.dumps(
                {
                    "error": "Access denied: File path is outside the allowed directory.",
                    "file_path": file_path,
                    "base_directory": base_dir,
                    "status": "error",
                })

        original_content = ""
        try:
            if os.path.exists(resolved_path):
                with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                    original_content = f.read()
            else:
                # If the file doesn't exist, the diff will show the entire new
                # content as additions
                print(f"Note: File '{resolved_path}' does not exist. Diff will show all content as new.")
        except Exception as e:
            warn_msg = "Warning: Could not read original file for diff "
            warn_msg += "'{}': {}".format(resolved_path, e)
            print(warn_msg)
            # Proceed with empty original_content to show full new content as
            # diff

        original_lines = original_content.splitlines()
        proposed_lines = proposed_new_content.splitlines()

        diff = difflib.unified_diff(original_lines, proposed_lines, lineterm="")

        colored_diff_lines = []
        for line in diff:
            if line.startswith("+"):
                colored_diff_lines.append(
                    "{0}{1}{2}".format(TermColors.GREEN, line, TermColors.RESET)
                )
            elif line.startswith("-"):
                colored_diff_lines.append(
                    "{0}{1}{2}".format(TermColors.RED, line, TermColors.RESET)
                )
            elif line.startswith("@"):
                colored_diff_lines.append(
                    "{0}{1}{2}".format(TermColors.CYAN, line, TermColors.RESET)
                )
            else:
                colored_diff_lines.append(line)

        colored_diff = "\n".join(colored_diff_lines)

        if not colored_diff:
            return json.dumps(
                {
                    "file_path": file_path,
                    "resolved_path": resolved_path,
                    "diff": "No changes proposed or file does not exist.",
                    "status": "no_change",
                }
            )

        return json.dumps(
            {
                "file_path": file_path, 
                "resolved_path": resolved_path,
                "diff": colored_diff, 
                "status": "success"
            }
        )

    except Exception as e:
        print("Error in get_diff_for_proposed_changes: {}".format(e))
        traceback.print_exc()
        return json.dumps(
            {"error": str(e), "file_path": file_path, "status": "error"}
        )


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "get_diff_for_proposed_changes",
            "description": "Compares proposed new content for a file with its current "
                           "content on disk and returns a unified diff (colorized for "
                           "terminal display). This helps visualize changes before they "
                           "are written. Paths are relative to the current working "
                           "directory or focus directory if one is set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The relative path to the file being changed "
                                       "or created.",
                    },
                    "proposed_new_content": {
                        "type": "string",
                        "description": "The full proposed new content for the file.",
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
                    "proposed_new_content"],
            },
        },
    }

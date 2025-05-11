import json
import os
import traceback
import git # Import the git library

def status():
    """
    Retrieves the Git repository status using GitPython.

    Returns:
        str: A JSON string containing the status or an error message.
    """
    print("--- TOOL EXECUTING: status() ---")
    try:
        repo = git.Repo('.') # Instantiate a Repo object for the current directory

        # Get changes
        # unstaged changes: compare index with working directory
        unstaged_changes = [diff.a_path for diff in repo.index.diff(None)]
        # staged changes: compare index with HEAD
        staged_changes = [diff.a_path for diff in repo.index.diff("HEAD")]
        # untracked files
        untracked_files = repo.untracked_files

        changes = {
            "staged": staged_changes,
            "unstaged": unstaged_changes,
            "untracked": untracked_files
        }

        return json.dumps({
            "status": "success",
            "changes": changes
        })

    except Exception as e:
        print(f"Error in status: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error",
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "status",
            "description": "Retrieves the Git repository status.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

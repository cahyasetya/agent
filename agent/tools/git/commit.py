import json
import os
import traceback

def commit(message: str, all_changes: bool = False):
    """
    Commits changes to the Git repository.

    Args:
        message (str): The commit message.
        all_changes (bool): Whether to automatically stage all modified and deleted files.

    Returns:
        str: A JSON string indicating success or an error message.
    """
    print(f"--- TOOL EXECUTING: commit(message='{message}', all_changes='{all_changes}') ---")
    try:
        # TODO: Implement the actual git commit command execution
        # import subprocess
        # command = ['git', 'commit', '-m', message]
        # if all_changes:
        #     command.append('-a')
        # result = subprocess.run(command, capture_output=True, text=True, check=True)
        # return json.dumps({
        #     "status": "success",
        #     "message": result.stdout.strip(),
        #     "error": result.stderr.strip(),
        # })

        # Placeholder response
        action = "Committing all changes" if all_changes else "Committing staged changes"
        message = f"{action} with message: '{message}'"

        return json.dumps({
            "status": "success",
            "message": message,
        })

    except Exception as e:
        print(f"Error in commit: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error",
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "commit",
            "description": "Commits changes to the Git repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The commit message."
                    },
                    "all_changes": {
                        "type": "boolean",
                        "description": "Whether to automatically stage all modified and deleted files."
                    }
                },
                "required": ["message"],
            }
        }
    }

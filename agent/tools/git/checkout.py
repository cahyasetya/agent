import json
import os
import traceback
import git

def checkout(branch_or_path, force=False, create_new_branch=False):
    """
    Checks out a Git branch or restores working tree files using GitPython.

    Args:
        branch_or_path (str): The branch to checkout or the path to restore.
        force (bool, optional): Whether to force the checkout (e.g., discard local changes). Defaults to False.
        create_new_branch (bool, optional): Whether to create a new branch before checking out. Defaults to False.

    Returns:
        str: A JSON string containing the checkout status and information or an error message.
    """
    print(f"--- TOOL EXECUTING: checkout(branch_or_path={branch_or_path}, force={force}, create_new_branch={create_new_branch}) ---")
    try:
        repo = git.Repo('.')

        if create_new_branch:
            # Create and checkout a new branch
            repo.git.checkout('-b', branch_or_path)
            message = f"Successfully created and checked out new branch '{branch_or_path}'."
        else:
            # Checkout existing branch or path
            options = [branch_or_path]
            if force:
                options.insert(0, '-f')
            repo.git.checkout(*options)
            message = f"Successfully checked out '{branch_or_path}'."

        return json.dumps({
            "status": "success",
            "message": message
        })

    except git.GitCommandError as e:
        print(f"Git command error in checkout: {e}")
        # Attempt to parse the error message for more helpful output
        error_message = str(e)
        if "did not match any file(s) known to git" in error_message:
             user_message = f"Error: Branch or path '{branch_or_path}' not found."
        elif "Your local changes to the following files would be overwritten" in error_message:
             user_message = f"Error: Your local changes would be overwritten by checking out '{branch_or_path}'. Commit or stash your changes or use the 'force' option to discard them."
        else:
            user_message = f"Error executing git checkout: {error_message}"


        return json.dumps({
            "error": user_message,
            "status": "error",
            "git_error": error_message # Include raw git error for debugging
        })
    except Exception as e:
        print(f"Error in checkout: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error"
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "checkout",
            "description": "Checks out a Git branch or restores working tree files.",
            "parameters": {
                "type": "object",
                "required": [
                    "branch_or_path"
                ],
                "properties": {
                    "branch_or_path": {
                        "type": "string",
                        "description": "The branch to checkout or the path to restore."
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Whether to force the checkout (e.g., discard local changes)."
                    },
                     "create_new_branch": {
                        "type": "boolean",
                        "description": "Whether to create a new branch before checking out."
                    }
                }
            }
        }
    }

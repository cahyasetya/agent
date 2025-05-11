import json
import os
import traceback
import git

def pull(branch=None, remote='origin'):
    """
    Pulls changes from a remote Git repository using GitPython.

    Args:
        branch (str, optional): The name of the branch to pull. Defaults to None (pulls all configured branches).
        remote (str, optional): The name of the remote repository. Defaults to 'origin'.

    Returns:
        str: A JSON string containing the pull status and information or an error message.
    """
    print(f"--- TOOL EXECUTING: pull(branch={branch}, remote={remote}) ---")
    try:
        repo = git.Repo('.')

        # Get the remote
        try:
            origin = repo.remotes[remote]
        except IndexError:
            return json.dumps({
                "status": "error",
                "message": f"Error: Remote '{remote}' not found."
            })

        # Pull changes
        if branch:
            info = origin.pull(branch)
        else:
            info = origin.pull()

        # Prepare response data
        # The info object from pull() is a list of UpdateProgress objects
        # We can extract relevant information like fetched commits,
        # changed files, etc. For simplicity, we'll just indicate success
        # and potentially include some basic info if available.

        # You might want to add more detailed parsing of the info object
        # depending on what information you need to return.
        pulled_branches = [str(i.ref) for i in info]

        return json.dumps({
            "status": "success",
            "message": f"Successfully pulled from {remote}.",
            "pulled_branches": pulled_branches
        })

    except Exception as e:
        print(f"Error in pull: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error"
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "pull",
            "description": "Pulls changes from a remote Git repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch": {
                        "type": "string",
                        "description": "The name of the branch to pull (default: current branch)."
                    },
                    "remote": {
                        "type": "string",
                        "description": "The name of the remote repository (default: 'origin')."
                    }
                }
            }
        }
    }

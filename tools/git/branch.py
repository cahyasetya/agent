import json
import os
import traceback
import subprocess

def list_branches():
    """
    Lists existing Git branches.

    Returns:
        str: A JSON string containing the list of branches or an error message.
    """
    print("--- TOOL EXECUTING: list_branches() ---")
    try:
        # Implement the actual git branch command execution to list branches
        command = ['git', 'branch']
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        branches = [branch.strip() for branch in result.stdout.strip().splitlines()]

        return json.dumps({
            "status": "success",
            "branches": branches
        })

        # Placeholder response
        # placeholder_branches = ["main", "development", "feature/new-feature"]
        # return json.dumps({
        #     "status": "success",
        #     "branches": placeholder_branches
        # })

    except Exception as e:
        print(f"Error in list_branches: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error",
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "list_branches",
            "description": "Lists existing Git branches.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

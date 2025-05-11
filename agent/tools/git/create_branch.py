import json
import os
import traceback
import subprocess

def create_branch(branch_name: str):
    """
    Creates a new Git branch.

    Args:
        branch_name: The name of the new branch.

    Returns:
        str: A JSON string indicating success or failure.
    """
    print(f"--- TOOL EXECUTING: create_branch(branch_name='{branch_name}') ---")
    try:
        command = ['git', 'branch', branch_name]
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        if result.returncode == 0:
            return json.dumps({
                "status": "success",
                "message": f"Branch '{branch_name}' created successfully."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": result.stderr.strip()
            })

    except subprocess.CalledProcessError as e:
        print(f"Error creating branch '{branch_name}': {e}")
        return json.dumps({
            "error": str(e),
            "status": "error",
            "message": f"Failed to create branch '{branch_name}'. Git command failed."
        })
    except Exception as e:
        print(f"Error in create_branch: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error",
            "message": f"An unexpected error occurred while creating branch '{branch_name}'."
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "create_branch",
            "description": "Creates a new Git branch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {
                        "type": "string",
                        "description": "The name of the new branch."
                    }
                },
                "required": ["branch_name"]
            }
        }
    }

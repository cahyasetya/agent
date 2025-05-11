import json
import os
import traceback
import git  # Import the git library

def log(max_count: int = 10, pretty: str = "oneline"):
    """
    Retrieves the Git commit log using GitPython.

    Args:
        max_count (int): The maximum number of log entries to return.
        pretty (str): Format of the log. Note: GitPython's pretty format handling might differ slightly from the command line.

    Returns:
        str: A JSON string containing the log entries or an error message.
    """
    print(f"--- TOOL EXECUTING: log(max_count='{max_count}', pretty='{pretty}') ---")
    try:
        repo = git.Repo('.')  # Assumes the tool is run in the repository root

        # GitPython's log method directly returns commit objects
        # We'll format them manually based on the 'pretty' option if supported,
        # or just return commit information.
        log_entries = []
        for commit in repo.iter_commits(max_count=max_count):
            if pretty == "oneline":
                log_entries.append(f"{commit.hexsha[:8]} {commit.summary}")
            elif pretty == "short":
                log_entries.append(f"commit {commit.hexsha}\nAuthor: {commit.author.name} <{commit.author.email}>\n\n    {commit.summary}")
            elif pretty == "medium":
                 log_entries.append(f"commit {commit.hexsha}\nAuthor: {commit.author.name} <{commit.author.email}>\nDate:   {commit.authored_datetime.strftime('%a %b %d %H:%M:%S %Y %z')}\n\n    {commit.summary}")
            elif pretty == "full":
                log_entries.append(f"commit {commit.hexsha}\nAuthor: {commit.author.name} <{commit.author.email}>\nCommit: {commit.committer.name} <{commit.committer.email}>\nDate:   {commit.authored_datetime.strftime('%a %b %d %H:%M:%S %Y %z')}\n\n    {commit.summary}")
            elif pretty == "fuller":
                log_entries.append(f"commit {commit.hexsha}\nAuthor: {commit.author.name} <{commit.author.email}>\nAuthorDate: {commit.authored_datetime.strftime('%a %b %d %H:%M:%S %Y %z')}\nCommit: {commit.committer.name} <{commit.committer.email}>\nCommitDate: {commit.committed_datetime.strftime('%a %b %d %H:%M:%S %Y %z')}\n\n    {commit.summary}")
            else:
                # Default to oneline or provide basic info for unsupported formats
                log_entries.append(f"{commit.hexsha[:8]} {commit.summary}")


        return json.dumps({
            "status": "success",
            "log": log_entries,
        })

    except git.exc.InvalidGitRepositoryError:
        return json.dumps({
            "error": "Not a git repository.",
            "status": "error",
        })
    except Exception as e:
        print(f"Error in log: {e}")
        traceback.print_exc()
        return json.dumps({
            "error": str(e),
            "status": "error",
        })

def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "log",
            "description": "Retrieves the Git commit log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_count": {
                        "type": "integer",
                        "description": "The maximum number of log entries to return."
                    },
                    "pretty": {
                        "type": "string",
                        "description": "Format of the log. Can be 'oneline', 'short', 'medium', 'full', 'fuller', or a custom format string."
                    }
                },
            }
        }
    }

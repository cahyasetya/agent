import json
import os

from rich.console import Console
from rich.syntax import Syntax


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "syntax_highlight",
            "description": "Highlight syntax of a file based on its extension",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to highlight",
                    },
                    "line_numbers": {
                        "type": "boolean",
                        "description": "Whether to show line numbers",
                        "default": True,
                    },
                },
                "required": ["file_path"],
            },
        },
    }


def syntax_highlight(file_path, line_numbers=True):
    """
    Highlight the syntax of a file based on its extension

    Args:
        file_path (str): Path to the file to highlight
        line_numbers (bool): Whether to show line numbers

    Returns:
        str: JSON string containing the highlighted content or error message
    """
    try:
        # Verify file exists
        if not os.path.isfile(file_path):
            return json.dumps({"error": f"File '{file_path}' not found"})

        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Determine the lexer based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()

        # Map file extensions to languages
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "bash",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".ts": "typescript",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".sql": "sql",
            ".toml": "toml",
            ".ini": "ini",
        }

        language = extension_map.get(file_extension, "text")

        # Create a console to capture the output
        console = Console(record=True, width=100)

        # Create a syntax object with the content and language
        syntax = Syntax(
            content,
            language,
            line_numbers=line_numbers,
            theme="monokai",
            word_wrap=True,
        )

        # Print the syntax object to the console
        console.print(syntax)

        # Get the string representation with ANSI codes
        output = console.export_text()

        return json.dumps({"formatted_output": output, "language": language})

    except Exception as e:
        return json.dumps({"error": f"Error highlighting file: {str(e)}"})

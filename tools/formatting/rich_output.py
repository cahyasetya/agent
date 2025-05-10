import json

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax


def get_tool_definition():
    return {
        "type": "function",
        "function": {
            "name": "rich_output",
            "description": "Format text for rich terminal display with syntax highlighting",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The text content to format",
                    },
                    "format_type": {
                        "type": "string",
                        "description": "The format type: 'code', 'markdown', 'panel', or 'syntax'",
                        "enum": ["code", "markdown", "panel", "syntax"],
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language for syntax highlighting (python, javascript, etc.)",
                        "default": "python",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title for panels",
                        "default": "",
                    },
                },
                "required": ["content", "format_type"],
            },
        },
    }


def rich_output(content, format_type, language="python", title=""):
    """
    Format text for rich terminal display with syntax highlighting

    Args:
        content (str): The text content to format
        format_type (str): The format type: 'code', 'markdown', 'panel', or 'syntax'
        language (str): Programming language for syntax highlighting
        title (str): Optional title for panels

    Returns:
        str: JSON string with formatted content (with ANSI escape sequences)
    """
    console = Console(highlight=True, record=True)

    try:
        # Create a string buffer by recording console output
        with console.capture() as capture:
            if format_type == "code" or format_type == "syntax":
                syntax = Syntax(content, language, line_numbers=True, theme="monokai")
                console.print(syntax)
            elif format_type == "markdown":
                md = Markdown(content)
                console.print(md)
            elif format_type == "panel":
                panel = Panel(content, title=title, border_style="bright_blue")
                console.print(panel)
            else:
                console.print(content)

        # Get the captured output with ANSI codes
        output = capture.get()

        return json.dumps({"formatted_output": output})

    except Exception as e:
        return json.dumps({"error": f"Error formatting output: {str(e)}"})

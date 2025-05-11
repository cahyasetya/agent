"""
Console utilities for the agent application.
Provides rich console output, formatting, and UI components.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

# --- Rich Console Setup for Colorful Output ---
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "command": "bold magenta",
        "prompt": "green",
        "system": "bright_blue",
        "user": "bright_white",
        "tool": "bright_yellow",
        "assistant": "bright_green",
    }
)

console = Console(theme=custom_theme, highlight=True)

def display_logo():
    """
    Display the application logo.
    """
    logo = """
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║   🤖 File System Agent with AI Assistance 🤖  ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
    """
    console.print(Panel(logo, border_style="bright_blue", expand=False))


def display_available_tools(tool_defs):
    """
    Display all available tools in a nice table.
    
    Args:
        tool_defs (list): List of tool definitions to display
    """
    tools_table = Table(title="📋 Available Tools", border_style="bright_blue")
    tools_table.add_column("Tool Name", style="bright_cyan")
    tools_table.add_column("Description", style="bright_white")
    tools_table.add_column("Category", style="bright_magenta")

    # Categorize tools
    file_ops_tools = []
    formatting_tools = []
    conversation_tools = []
    other_tools = []

    for tool_def in tool_defs:
        if isinstance(tool_def, dict) and "function" in tool_def:
            function_def = tool_def["function"]
            name = function_def.get("name", "Unknown")
            description = function_def.get(
                "description", "No description available"
            )

            # Categorize based on module path or name
            if "file_operations" in str(tool_def):
                file_ops_tools.append((name, description))
            elif "formatting" in str(tool_def):
                formatting_tools.append((name, description))
            elif name in ["dump_messages", "load_messages"] or "conversation" in str(tool_def):
                conversation_tools.append((name, description))
            else:
                other_tools.append((name, description))

    # Add file operation tools
    for name, description in file_ops_tools:
        tools_table.add_row(name, description, "File Operations")

    # Add formatting tools
    for name, description in formatting_tools:
        tools_table.add_row(name, description, "Formatting")

    # Add conversation tools
    for name, description in conversation_tools:
        tools_table.add_row(name, description, "Conversation")

    # Add other tools
    for name, description in other_tools:
        tools_table.add_row(name, description, "Miscellaneous")

    console.print(tools_table)


def display_help():
    """
    Display help information for the user.
    """
    help_text = """
    [bold cyan]Available Commands:[/bold cyan]
    
    [command]exit[/command] or [command]quit[/command] - Exit the application
    [command]save [filename][/command] - Save the conversation to a file
    [command]load <filename>[/command] - Load a conversation from a file
    [command]clear[/command] - Clear the conversation history
    [command]help[/command] - Show this help message
    """
    console.print(Panel(help_text, border_style="bright_blue", title="📚 Help"))

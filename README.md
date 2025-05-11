# Python Agents Project

This agent built using AI. A modular Python agent system with AI assistance for file system operations, code editing, and project management.

## Overview

This project provides an intelligent agent that can help with:

- File system operations and management
- Code editing, refactoring, and review
- Project exploration and navigation
- Conversation persistence for long-term assistance

The agent uses the OpenRouter API to access large language models like Google Gemini 2.5, and provides a command-line interface with rich terminal output.

## Features

- **AI-powered assistance**: Uses LLMs through OpenRouter for intelligent decision making
- **File operations**: Read, write, create, move, and search for files with AI assistance
- **Directory focus**: Focus on specific directories for project-scoped operations
- **Conversation persistence**: Save and load conversations to continue work later
- **Rich terminal UI**: Colorful, formatted output for better readability
- **Command system**: Built-in commands for common operations
- **Modular architecture**: Well-organized code for easy extension and maintenance

## Architecture

The project is organized into modular components:

- **main.py**: Application entry point with main loop logic
- **agent/**: Core module with agent components
  - **api.py**: API client for LLM
  - **console.py**: Console UI utilities 
  - **commands.py**: Special command handling
  - **conversation.py**: Conversation saving and loading
  - **tools.py**: Tool discovery and management
- **tools/**: Modular tools that the agent can use
  - **file_operations/**: File system related tools
  - **formatting/**: Output formatting tools
  - **git/**: Git-related tools
  - **shared/**: Shared utilities for all tools

## Setup

1. Ensure Python 3.8+ is installed (using pyenv is recommended)
2. Set up the environment:
   ```bash
   # Create virtual environment (if not already created)
   pyenv virtualenv 3.10.0 agents-env
   
   # Activate the environment
   pyenv local agents-env
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. Set up your OpenRouter API key:
   ```bash
   # Add to your .env file
   echo "OPENROUTER_API_KEY=your_openrouter_api_key_here" >> .env
   
   # Or set it in your environment
   export OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```

## Usage

Run the agent with various options:

```bash
# Basic usage
python main.py

# Focus on a specific directory
python main.py --path /path/to/your/project

# Load a previous conversation
python main.py --load conversation_name
```

Or use the provided Makefile:

```bash
# Run with default settings
make run

# Focus on a specific directory
make run-focused PATH=/path/to/your/project

# Load a previous conversation
make load-conversation CONV=conversation_name
```

## Available Commands

During an agent session, you can use these commands:

- `exit` or `quit`: Exit the application
- `save [filename]`: Save the conversation to a file
- `load <filename>`: Load a conversation from a file
- `clear`: Clear the conversation history
- `help`: Show help information

## Environment Variables

Configure the `.env` file to set up your environment variables:
- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `LLM_MODEL`: Model to use (default: "google/gemini-2.5-flash-preview")

## Extending the Agent

To add new capabilities to the agent, add new tool modules in the `tools/` directory. Each tool should have:

1. A main function that implements the tool's functionality
2. A `get_tool_definition()` function that returns the tool's schema

Example tool:

```python
import json

def my_tool(param1, param2):
    """Implement the tool's functionality"""
    # ... implementation ...
    return json.dumps({"result": "Tool executed successfully"})

def get_tool_definition():
    """Define the tool's schema"""
    return {
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "Description of what the tool does",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of param1",
                    },
                    "param2": {
                        "type": "number",
                        "description": "Description of param2",
                    },
                },
                "required": ["param1", "param2"],
            },
        },
    }
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

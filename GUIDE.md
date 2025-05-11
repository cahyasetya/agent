# Agent User Guide

This guide provides detailed instructions on how to use the File System Agent with AI Assistance effectively.

## Getting Started

### Prerequisites

Before starting, make sure you have:

1. Python 3.8 or higher installed
2. An OpenRouter API key with access to Google Gemini 2.5 or compatible models
3. The project dependencies installed (`pip install -r requirements.txt`)

### First Run

To start the agent with basic settings:

```bash
python main.py
```

You'll see:
- A welcome screen with available commands
- A list of available tools the agent can use
- A prompt where you can start typing your requests

## Core Features

### Directory Focus

The agent can focus on a specific directory for all file operations. This is useful when working on a project.

```bash
python main.py --path /path/to/your/project
```

When focused on a directory:
- All file paths are relative to the focus directory by default
- The agent prioritizes operations within this directory
- You can still access files outside by setting `use_focus_path=False` in tool calls

### Conversation Persistence

One of the most powerful features is the ability to save and load conversations:

**Saving a conversation:**
```
You > save my_project_refactoring
```

**Loading a conversation:**
```
You > load my_project_refactoring
```

You can also load a conversation when starting the agent:
```bash
python main.py --load my_project_refactoring
```

This feature lets you:
- Continue complex work across multiple sessions
- Maintain context for ongoing projects
- Share conversations with team members

### Command System

The agent provides built-in commands for common operations:

| Command | Description |
|---------|-------------|
| `exit` or `quit` | Exit the application |
| `save [filename]` | Save conversation to a file |
| `load <filename>` | Load a conversation from a file |
| `clear` | Clear conversation history |
| `help` | Show help information |

## Working with Files

### Reading Files

To read a file, you can simply ask:

```
You > Can you show me the content of config.py?
```

### Editing Files

The agent follows a safe workflow for file editing:

1. First, it reads the current file content
2. It then creates a proposed new version based on your request
3. It shows you a diff of the changes
4. Only after your confirmation does it write the changes

Example:

```
You > Refactor the read_file_content function in tools/file_operations/read_file_content.py to be more efficient
```

### Creating Files

You can ask the agent to create new files:

```
You > Create a new Python file called data_processor.py that can parse CSV files
```

### Organizing Files

The agent can help organize your project:

```
You > Move all .py files from the current directory to a new folder called src
```

## Advanced Usage

### Code Refactoring

For complex refactoring, be specific about what you want to change:

```
You > Refactor agent/tools.py to split the get_available_functions method into smaller, more focused functions
```

### Project Exploration

The agent can help you understand project structure:

```
You > Analyze the project structure and give me an overview of the main components
```

### Multiple File Operations

You can ask for operations involving multiple files:

```
You > Find all files that import the 'requests' library and add proper error handling
```

## Extending the Agent

To add new capabilities, create tool modules in the `tools/` directory:

1. Create a new Python file in the appropriate subdirectory
2. Implement your tool function
3. Add a `get_tool_definition()` function
4. The agent will automatically discover and load your tool

## Troubleshooting

### Common Issues

**API Key Issues:**
- Ensure `OPENROUTER_API_KEY` is set in your environment or .env file
- Check that your key has access to the required models

**File Permission Issues:**
- The agent can only access files you have permission to read/write
- Some operations may require running with appropriate permissions

**Path Resolution Issues:**
- When using focus paths, ensure paths are correctly specified
- Use `use_focus_path=False` if you need to access files outside the focus directory

## Best Practices

1. **Be Specific**: Provide clear instructions for best results
2. **Review Changes**: Always review diffs before confirming file changes
3. **Use Conversation Saving**: Save important conversations for long-running tasks
4. **Focus on Directories**: Use directory focus for project-specific work
5. **Check Tool Results**: Verify tool outputs for correctness

## Getting Help

If you're stuck, you can:
- Type `help` to see available commands
- Ask the agent for assistance with specific tools
- Check the project README.md for more information

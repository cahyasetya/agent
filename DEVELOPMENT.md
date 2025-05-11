# Developer Guide

This guide provides information for developers who want to modify, extend, or contribute to the File System Agent project.

## Project Architecture

The project follows a modular architecture organized into the following components:

### Core Structure

- **main.py**: Application entry point with main loop and orchestration
- **agent/**: Core module with agent components
  - **__init__.py**: Module exports and version info
  - **api.py**: API client for LLM interaction
  - **console.py**: Console UI utilities
  - **commands.py**: Special command handling
  - **conversation.py**: Conversation saving and loading
  - **tools.py**: Tool discovery and management
- **tools/**: Modular tools that the agent can use
  - **file_operations/**: File system related tools
  - **formatting/**: Output formatting tools
  - **git/**: Git-related tools
  - **shared/**: Shared utilities for all tools

### Control Flow

1. **Initialization**: 
   - Parse command-line arguments
   - Set up the environment and console
   - Initialize system message and conversation state
   
2. **Main Loop**:
   - Get user input
   - Handle special commands if needed
   - Otherwise, send to LLM for processing
   - Process any tool calls from the LLM
   - Display the final response

3. **Tool Execution**:
   - Tools are discovered dynamically
   - Each tool must return JSON-serializable results
   - Tools use shared utilities for common operations

## Adding New Features

### Adding a New Tool

To add a new tool to the agent:

1. Create a new Python file in the appropriate subdirectory of `tools/`
2. Implement your tool function with proper error handling
3. Add a `get_tool_definition()` function that returns the OpenAI function schema

Example of a new tool:

```python
# tools/my_category/my_tool.py
import json
import traceback

def my_tool(param1, param2):
    """
    Implement your tool functionality.
    
    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2
        
    Returns:
        str: JSON string with the result
    """
    try:
        # Your implementation here
        result = {"param1": param1, "param2": param2, "success": True}
        return json.dumps(result)
    except Exception as e:
        print(f"Error in my_tool: {e}")
        traceback.print_exc()
        return json.dumps({"error": str(e), "status": "error"})

def get_tool_definition():
    """
    Define the tool schema for the LLM.
    """
    return {
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "A detailed description of what this tool does",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of param1",
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Description of param2",
                    },
                },
                "required": ["param1", "param2"],
            },
        },
    }
```

### Modifying Core Components

To modify core agent functionality:

1. **API Client**: Modify `agent/api.py` to change how the agent interacts with LLMs
2. **Console UI**: Update `agent/console.py` for changes to the user interface
3. **Command Handling**: Edit `agent/commands.py` to add new commands
4. **Conversation Management**: Update `agent/conversation.py` to change saving/loading
5. **Tool Management**: Modify `agent/tools.py` to change tool discovery or execution

### Adding New Commands

To add a new special command:

1. Open `agent/commands.py`
2. Update the `handle_special_command()` function with your new command
3. Add your command's implementation
4. Update the `display_help()` function in `agent/console.py` to document your command

Example:

```python
# In agent/commands.py
elif base_cmd == "my_command":
    # Implement your command here
    console.print("[success]My command executed successfully[/success]")
    return True

# In agent/console.py, update the help text:
help_text = """
...
[command]my_command[/command] - Description of my new command
...
"""
```

## Debugging and Testing

### Enabling Debug Output

Add debug logging:

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO)
logger = logging.getLogger(__name__)

# Use throughout the code
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### Testing Tools

Each tool should be testable in isolation. Create test files in a `tests/` directory:

```python
# tests/test_my_tool.py
import json
import unittest
from tools.my_category.my_tool import my_tool

class TestMyTool(unittest.TestCase):
    def test_my_tool_success(self):
        result = my_tool("test", 42)
        result_dict = json.loads(result)
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["param1"], "test")
        self.assertEqual(result_dict["param2"], 42)
    
    def test_my_tool_failure(self):
        # Test edge cases and error handling
        pass

if __name__ == "__main__":
    unittest.main()
```

## Best Practices

### Code Style

- Follow PEP 8 guidelines
- Use docstrings for all functions and classes
- Add type hints for better code readability
- Use meaningful variable and function names

### Error Handling

- Always wrap tool implementations in try/except blocks
- Return structured error messages as JSON
- Log detailed errors with traceback for debugging
- Handle gracefully to avoid crashing the main loop

### Security Considerations

- Validate all file paths to prevent directory traversal
- Use `resolve_path` utility for path resolution
- Never execute arbitrary code from user input
- Limit file operations to allowed directories

### Performance Tips

- Keep tool functions lightweight and focused
- For heavy operations, consider adding progress indicators
- Cache results when appropriate
- Profile slow operations to identify bottlenecks

## Documentation

When adding new features, remember to update:

1. Function and class docstrings
2. README.md for high-level documentation
3. GUIDE.md for user-facing changes
4. DEVELOPMENT.md (this file) for developer-focused documentation
5. Comments for complex code sections

## Deployment

To package the agent for distribution:

```bash
# Create a distributable package
pip install pyinstaller
pyinstaller --onefile main.py

# The executable will be in the dist/ directory
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Submit a pull request

Please follow the existing code style and add appropriate documentation and tests.

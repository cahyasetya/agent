"""
Tools management module for the agent.

This module is responsible for discovering and managing tool functions
that the agent can use for various operations.
"""

import importlib
import inspect
import os
import sys
from typing import Dict, Any, List

# Get all available tool functions
def get_available_functions(messages=None) -> Dict[str, Any]:
    """
    Get a dictionary of all available functions that can be called by the LLM.
    
    Args:
        messages (list, optional): The current message history, which might be
                                   needed by some functions.
    
    Returns:
        Dict[str, callable]: A dictionary mapping function names to their callables
    """
    # Start with basic functions
    available_functions = {}
    
    # Add tool functions from tools directory
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
    
    # Add tools directory to sys.path if it's not already there
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)
    
    # Look for subdirectories in the tools directory
    for subdir in os.listdir(tools_dir):
        subdir_path = os.path.join(tools_dir, subdir)
        
        # Skip non-directories and special directories (like __pycache__)
        if not os.path.isdir(subdir_path) or subdir.startswith('__'):
            continue
        
        # Check each Python file in the subdirectory
        for filename in os.listdir(subdir_path):
            # Skip non-Python files and __init__.py
            if not filename.endswith('.py') or filename == '__init__.py':
                continue
            
            module_name = f"agent.tools.{subdir}.{filename[:-3]}"  # Remove .py extension
            
            try:
                # Import the module dynamically
                module = importlib.import_module(module_name)
                
                # Find all functions defined in the module
                for name, obj in inspect.getmembers(module):
                    # Only include callable objects that don't start with underscore
                    if (callable(obj) and not name.startswith('_') 
                            and not name == 'get_tool_definition'):
                        
                        # Check if the function is directly defined in this module
                        # (not imported from elsewhere)
                        if obj.__module__ == module.__name__:
                            available_functions[name] = obj
            
            except Exception as e:
                print(f"Error importing module {module_name}: {e}")
    
    return available_functions


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get definitions for all available tools that can be used by the LLM.
    
    Returns:
        List[Dict[str, Any]]: A list of tool definitions in the format expected by the LLM API
    """
    tool_definitions = []
    
    # Look for tools in the tools directory
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
    
    # Add tools directory to sys.path if it's not already there
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)
    
    # Look for subdirectories in the tools directory
    for subdir in os.listdir(tools_dir):
        subdir_path = os.path.join(tools_dir, subdir)
        
        # Skip non-directories and special directories
        if not os.path.isdir(subdir_path) or subdir.startswith('__'):
            continue
        
        # Check each Python file in the subdirectory
        for filename in os.listdir(subdir_path):
            # Skip non-Python files and __init__.py
            if not filename.endswith('.py') or filename == '__init__.py':
                continue
            
            module_name = f"agent.tools.{subdir}.{filename[:-3]}"  # Remove .py extension
            
            try:
                # Import the module dynamically
                module = importlib.import_module(module_name)
                
                # Check if the module has a get_tool_definition function
                if hasattr(module, 'get_tool_definition'):
                    # Get the tool definition
                    definition = module.get_tool_definition()
                    
                    # Add it to the list (it might be a single definition or a list)
                    if isinstance(definition, list):
                        tool_definitions.extend(definition)
                    else:
                        tool_definitions.append(definition)
            
            except Exception as e:
                print(f"Error importing module {module_name}: {e}")
    
    return tool_definitions

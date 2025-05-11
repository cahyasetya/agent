""""
Tool management utilities.
Provides functionality to discover, load, and manage tools.
"""

import importlib.util
import os
import logging
import sys
import traceback
from typing import Dict, List, Any, Tuple, Callable

from .console import console
from .conversation import dump_messages_to_file, load_messages_from_file
from tools.file_operations.create_empty_file import create_empty_file
from tools.file_operations.move_files import move_files
from tools.file_operations.read_file_content import read_file_content
from tools.file_operations.write_to_file import write_to_file

# Set up a basic logger
logger = logging.getLogger(__name__)

def find_all_tool_modules():
    """
    Scan all subdirectories in the tools directory for Python modules with
    get_tool_definition
    
    Returns:
        dict: Dictionary mapping function names to (module, module_path) tuples
    """
    all_tool_modules = {}
    tools_dir = "tools"

    if not os.path.exists(tools_dir):
        logger.warning(f"Tools directory '{tools_dir}' not found.")
        return all_tool_modules

    # First, add tools directory itself to sys.path
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)

    # Function to explore a directory and find tool modules
    def explore_dir(directory):
        modules_found = {}

        # List all Python files in this directory
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)

            # If it's a directory with __init__.py, explore it recursively
            init_path = os.path.join(item_path, "__init__.py")
            if os.path.isdir(item_path) and os.path.exists(init_path):
                # Recursively explore the subdirectory and add its modules
                sub_modules = explore_dir(item_path)
                modules_found.update(sub_modules)

            # If it's a Python file, try to load it
            elif item.endswith(".py") and item != "__init__.py":
                # Get the module name without .py extension
                module_name = item[:-3]

                # Calculate the full module path
                rel_path = os.path.relpath(
                    os.path.dirname(item_path), start=os.getcwd()
                )
                full_module_path = (
                    f"{rel_path.replace(os.path.sep, '.')}.{module_name}"
                )

                try:
                    # Use importlib to import the module
                    module = importlib.import_module(full_module_path)

                    # Check if it has the get_tool_definition function
                    has_tool_def = (hasattr(module, "get_tool_definition") and
                                    callable(module.get_tool_definition))
                    if has_tool_def:
                        # Store the module with its function name for later
                        function_name = None

                        # Try to determine the function name from the tool def
                        try:
                            tool_def = module.get_tool_definition()
                            if isinstance(tool_def, list):
                                # Handle multiple tools in one module
                                for single_def in tool_def:
                                    if (isinstance(single_def, dict) and
                                            "function" in single_def):
                                        subfunc_name = single_def["function"].get("name")
                                        if subfunc_name:
                                            # Store each function separately
                                            modules_found[subfunc_name] = (
                                                module,
                                                full_module_path
                                            )
                                # Continue to next item since we've handled this module
                                continue
                            
                            # Single tool definition
                            is_tool_dict = (isinstance(tool_def, dict) and
                                            "function" in tool_def)
                            if is_tool_dict:
                                function_name = tool_def["function"].get("name")
                        except Exception:
                            pass

                        # If we couldn't get the name, use the module name
                        if not function_name:
                            function_name = module_name

                        modules_found[function_name] = (
                            module,
                            full_module_path,
                        )
                except Exception as e:
                    warning_msg = "[warning]Could not load module "
                    warning_msg += f"{full_module_path}: {e}[/warning]"
                    console.print(warning_msg)

        return modules_found

    # Start the exploration at the tools directory
    all_tool_modules = explore_dir(tools_dir)

    # Remove tools directory from sys.path
    if tools_dir in sys.path:
        sys.path.remove(tools_dir)

    return all_tool_modules


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get all tool definitions from available modules.
    
    Returns:
        list: List of tool definitions
    """
    tool_definitions = []
    tool_modules = find_all_tool_modules()

    for function_name, (module, module_path) in tool_modules.items():
        try:
            has_tool_def = (hasattr(module, "get_tool_definition") and
                            callable(module.get_tool_definition))
            if has_tool_def:
                tool_def = module.get_tool_definition()
                # Add to list in appropriate format
                if isinstance(tool_def, list):
                    tool_definitions.extend(tool_def)
                else:
                    tool_definitions.append(tool_def)
                logger.debug(f"Loaded tool definition for '{function_name}' from {module_path}")
            else:
                logger.warning(f"Module {module_path} has no get_tool_definition function")
        except Exception as e:
            logger.error(f"Error loading tool definition from {module_path}: {e}")
            traceback.print_exc()

    return tool_definitions


def get_available_functions(messages: List[Dict[str, Any]]) -> Dict[str, Callable]:
    """
    Create a dictionary mapping function names to their callable implementations.
    
    Args:
        messages (list): Reference to the messages list for conversation functions
        
    Returns:
        dict: Dictionary mapping function names to their implementations
    """
    available_functions = {}
    tool_modules = find_all_tool_modules()

    # First, add our explicitly imported functions
    available_functions.update(
        {
            "read_file_content": read_file_content,
            "write_to_file": write_to_file,
            "create_empty_file": create_empty_file,
            "move_files": move_files,
        }
    )
    
    # Add our conversation functions with wrappers to access the messages list
    def dump_messages_wrapper(filename=None, use_focus_path=True):
        """Wrapper to provide access to the messages variable"""
        return dump_messages_to_file(messages, filename, use_focus_path)
    
    def load_messages_wrapper(filename, use_focus_path=True):
        """Wrapper to provide access to the messages variable"""
        result, loaded_messages = load_messages_from_file(filename, use_focus_path)
        if loaded_messages is not None:
            messages.clear()
            messages.extend(loaded_messages)
        return result
        
    available_functions.update({
        "dump_messages": dump_messages_wrapper,
        "load_messages": load_messages_wrapper,
    })

    # Then add dynamically discovered functions
    for function_name, (module, _) in tool_modules.items():
        # Skip our special message functions that are handled separately
        if function_name in ["dump_messages", "load_messages"]:
            continue
            
        # Check if the module has a function with the same name as the tool
        if hasattr(module, function_name) and callable(
            getattr(module, function_name)
        ):
            available_functions[function_name] = getattr(module, function_name)

    return available_functions

"""
Tools module for the AI agent.

This package contains various tools that the agent can use to perform operations
such as file system manipulation, formatting, git interactions, etc.
"""

# Import directly from the tools.py file by path to avoid circular imports
import importlib.util
import os
import sys

# Load the tools.py module directly to avoid circular imports
tools_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools.py")
spec = importlib.util.spec_from_file_location("tools_module", tools_path)
tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools_module)

# Export these functions as part of the package
get_tool_definitions = tools_module.get_tool_definitions
get_available_functions = tools_module.get_available_functions

# Version info
__version__ = "0.2.0"

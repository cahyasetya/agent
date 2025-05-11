"""Agent module for file system operations with AI assistance.
This module provides tools and utilities for interacting with the file system
and using LLMs to assist with file operations, refactoring, and management.
"""

# Export common symbols for easier imports
from .api import call_openrouter_api
from .console import display_logo, console
from .conversation import dump_messages_to_file, load_messages_from_file

# Don't import from .tools here to avoid circular imports
# The tools module will be available as agent.tools

# Version info
__version__ = "0.2.0"

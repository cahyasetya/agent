"""
Path utilities for the AI agent.

This module provides path resolution and manipulation utilities.
"""
import os

# Global variable to store the focus path across the application
# This will be set by agent.py and used by tool functions
FOCUS_PATH = None

def set_focus_path(path):
    """
    Set the global focus path for all tools to use
    Args:
        path (str): The absolute path to the directory to focus on
    """
    global FOCUS_PATH
    FOCUS_PATH = path
    print(f"Focus path set to: {FOCUS_PATH}")
    
def get_focus_path():
    """
    Get the currently set focus path
    Returns:
        str or None: The focus path if set, None otherwise
    """
    return FOCUS_PATH

def resolve_path(file_path, use_focus_path=True):
    """
    Resolve a relative path to an absolute path, using focus path if specified
    
    Args:
        file_path (str): The relative path to resolve
        use_focus_path (bool): Whether to use the focus path as base directory
        
    Returns:
        tuple: (resolved_path, base_dir, is_in_base_dir)
        - resolved_path: The absolute path
        - base_dir: The base directory used (focus path or cwd)
        - is_in_base_dir: Whether the resolved path is within the base directory
    """
    # Determine the base directory - either focus path or current working directory
    base_dir = FOCUS_PATH if (use_focus_path and FOCUS_PATH) else os.getcwd()
    
    # If file_path is already absolute, use it directly
    if os.path.isabs(file_path):
        resolved_path = file_path
    else:
        # Otherwise, join it with the base directory
        resolved_path = os.path.abspath(os.path.join(base_dir, file_path))
    
    # Check if the resolved path is within the base directory
    is_in_base_dir = resolved_path.startswith(base_dir)
    
    return resolved_path, base_dir, is_in_base_dir

def get_relative_path(abs_path, base_dir=None):
    """
    Convert an absolute path to a path relative to base_dir
    
    Args:
        abs_path (str): The absolute path to convert
        base_dir (str): The base directory to make the path relative to
                        (defaults to focus path or cwd)
                        
    Returns:
        str: The relative path
    """
    if base_dir is None:
        base_dir = FOCUS_PATH if FOCUS_PATH else os.getcwd()
    
    return os.path.relpath(abs_path, start=base_dir)

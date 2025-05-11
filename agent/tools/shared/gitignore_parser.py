"""Gitignore parser utilities for the AI agent.

This module provides functionality to parse .gitignore files and check if paths match gitignore patterns.
"""
import os
import fnmatch

def parse_gitignore(base_dir):
    """Parses a .gitignore file and returns a list of patterns to ignore.
    
    Args:
        base_dir (str): Directory where .gitignore is located
        
    Returns:
        list: List of patterns from the .gitignore file
    """
    patterns = []
    gitignore_path = os.path.join(base_dir, ".gitignore")
    
    if not os.path.exists(gitignore_path):
        # Add default patterns that should be ignored
        patterns.extend([
            "venv/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            ".git/",
            "*.egg-info/",
            "*.egg",
            "dist/",
            "build/",
            ".env"
        ])
        return patterns
    
    try:
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    except Exception as e:
        print(f"Error parsing .gitignore file: {e}")
        # Use default patterns as fallback
        patterns.extend([
            "venv/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            ".git/",
            "*.egg-info/",
            "*.egg",
            "dist/",
            "build/",
            ".env"
        ])
    
    # Ensure venv is in the patterns
    if "venv/" not in patterns and "venv" not in patterns:
        patterns.append("venv/")
    
    return patterns

def is_ignored(path, patterns):
    """Checks if a path should be ignored based on gitignore patterns.
    
    Args:
        path (str): Path to check
        patterns (list): List of gitignore patterns
        
    Returns:
        bool: True if the path should be ignored, False otherwise
    """
    # Convert path to relative path for matching
    name = os.path.basename(path)
    
    for pattern in patterns:
        # Handle directory-specific patterns
        is_dir_pattern = pattern.endswith("/")
        is_dir = os.path.isdir(path)
        
        # Strip trailing slash for matching
        if is_dir_pattern:
            pattern = pattern[:-1]
        
        # Direct name match
        if pattern == name:
            return True
        
        # Directory match only applies to directories
        if is_dir_pattern and not is_dir:
            continue
            
        # Handle simple wildcard patterns
        if fnmatch.fnmatch(name, pattern):
            return True
        
        # Check if any part of the path matches the pattern
        path_parts = path.split(os.path.sep)
        for i in range(len(path_parts)):
            subpath = os.path.sep.join(path_parts[i:])
            if fnmatch.fnmatch(subpath, pattern):
                return True
            
    return False

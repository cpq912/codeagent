import os
import fnmatch
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from codeagent.tools.registry import tool

class GrepArgs(BaseModel):
    pattern: str = Field(..., description="String pattern to search for")
    path: str = Field(".", description="Directory to search in (default: current dir)")
    case_sensitive: bool = Field(False, description="Whether search should be case sensitive")
    exclude_dirs: List[str] = Field(
        default_factory=lambda: [".git", ".venv", "__pycache__", "node_modules"],
        description="Directories to exclude"
    )

class GlobArgs(BaseModel):
    pattern: str = Field(..., description="Glob pattern (e.g. **/*.py)")
    path: str = Field(".", description="Root directory to search in")

@tool
def grep_search(args: GrepArgs) -> str:
    """
    Search for a string pattern in files (recursive).
    Returns 'FilePath:LineNumber: Content'.
    """
    results = []
    root_path = Path(args.path)
    
    if not root_path.exists():
        return f"Error: Path {root_path} does not exist"
    
    # Pre-process exclude dirs for faster lookup
    exclude_set = set(args.exclude_dirs)
    
    search_pattern = args.pattern if args.case_sensitive else args.pattern.lower()
    
    try:
        for root, dirs, files in os.walk(root_path):
            # Modify dirs in-place to prune excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_set and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip binary files or common non-text extensions could be added here
                # For MVP we try to read everything as text
                try:
                    # Try reading with utf-8, ignore errors to skip binary-like files
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            line_content = line if args.case_sensitive else line.lower()
                            if search_pattern in line_content:
                                # Truncate long lines
                                display_line = line.strip()[:200]
                                results.append(f"{file_path}:{i}: {display_line}")
                                
                                # Limit total results to prevent context overflow
                                if len(results) >= 100:
                                    results.append("... (results truncated after 100 matches)")
                                    return "\n".join(results)
                except Exception:
                    continue
                    
        if not results:
            return "No matches found."
            
        return "\n".join(results)
        
    except Exception as e:
        return f"Error during grep: {str(e)}"

@tool
def glob_search(args: GlobArgs) -> str:
    """
    Find files matching a glob pattern (e.g. **/*.py).
    """
    try:
        root_path = Path(args.path)
        if not root_path.exists():
            return f"Error: Path {root_path} does not exist"
            
        results = list(root_path.glob(args.pattern))
        
        if not results:
            return "No matching files found."
            
        # Convert to string paths and limit
        result_strs = [str(p) for p in results[:100]]
        if len(results) > 100:
            result_strs.append(f"... ({len(results) - 100} more files)")
            
        return "\n".join(result_strs)
        
    except Exception as e:
        return f"Error during glob: {str(e)}"

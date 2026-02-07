import os
from pathlib import Path
from pydantic import BaseModel, Field
from codeagent.tools.registry import tool

class ReadFileArgs(BaseModel):
    path: str = Field(..., description="Path to the file to read")

class WriteFileArgs(BaseModel):
    path: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")

class ListDirArgs(BaseModel):
    path: str = Field(".", description="Directory path to list")

@tool
def read_file(args: ReadFileArgs) -> str:
    """Read contents of a file."""
    try:
        path = Path(args.path)
        if not path.exists():
            return f"Error: File not found at {path}"
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(args: WriteFileArgs) -> str:
    """Write content to a file. Overwrites if exists."""
    try:
        path = Path(args.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args.content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def list_dir(args: ListDirArgs) -> str:
    """List files and directories in a given path."""
    try:
        path = Path(args.path)
        if not path.exists():
            return f"Error: Directory not found at {path}"
        
        entries = []
        for entry in path.iterdir():
            prefix = "[DIR] " if entry.is_dir() else "[FILE]"
            entries.append(f"{prefix} {entry.name}")
            
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

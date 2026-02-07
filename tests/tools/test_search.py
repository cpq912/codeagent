from codeagent.tools.search_tools import grep_search, glob_search, GrepArgs, GlobArgs
import os

def test_glob_search(tmp_path):
    # Setup files
    (tmp_path / "a.py").touch()
    (tmp_path / "b.txt").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "c.py").touch()
    
    # Test *.py
    res = glob_search(GlobArgs(pattern="**/*.py", path=str(tmp_path)))
    assert "a.py" in res
    assert "c.py" in res
    assert "b.txt" not in res

def test_grep_search(tmp_path):
    # Setup file with content
    f = tmp_path / "test.txt"
    f.write_text("Hello World\nAnother Line\nHello CodeAgent", encoding="utf-8")
    
    # Test search "Hello"
    res = grep_search(GrepArgs(pattern="Hello", path=str(tmp_path)))
    assert "test.txt:1: Hello World" in res
    assert "test.txt:3: Hello CodeAgent" in res
    assert "Another Line" not in res

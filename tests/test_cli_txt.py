"""Tests for svb2txt CLI."""

import json
from pathlib import Path
from svb2json.cli_txt import main, format_entry_as_text
import sys
from io import StringIO


def test_format_entry_as_text():
    """Test formatting a subtitle entry as text."""
    entry = {
        "id": 1,
        "start": 1000,
        "end": 5000,
        "text": "Hello world"
    }
    
    # Test with milliseconds
    result = format_entry_as_text(entry, "Mi", False)
    assert result == "[1000–5000] Hello world"
    
    # Test with HH:MM:SS format
    result = format_entry_as_text(entry, "HH:MM:SS", False)
    assert result == "[00:00:01–00:00:05] Hello world"
    
    # Test with seconds
    entry_seconds = {
        "id": 1,
        "start": 1,
        "end": 5,
        "text": "Hello world"
    }
    result = format_entry_as_text(entry_seconds, "HH:MM:SS", True)
    assert result == "[00:00:01–00:00:05] Hello world"


def test_format_entry_with_different_formats():
    """Test different timestamp formats."""
    entry = {
        "id": 1,
        "start": 3661000,  # 1:01:01
        "end": 3665000,    # 1:01:05
        "text": "Test text"
    }
    
    # HH:MM:SS.Mi format
    result = format_entry_as_text(entry, "HH:MM:SS.Mi", False)
    assert result == "[01:01:01.000–01:01:05.000] Test text"
    
    # HH:MM format
    result = format_entry_as_text(entry, "HH:MM", False)
    assert result == "[01:01–01:01] Test text"
    
    # SS format (seconds only)
    result = format_entry_as_text(entry, "SS", False)
    assert result == "[3661–3665] Test text"


def test_main_with_sample_file(tmp_path):
    """Test main function with a sample SBV file."""
    # Create a sample SBV file
    sbv_content = """0:00:01.000,0:00:03.000
First subtitle

0:00:04.000,0:00:06.000
Second subtitle
"""
    
    input_file = tmp_path / "test.sbv"
    output_file = tmp_path / "output.txt"
    
    input_file.write_text(sbv_content, encoding="utf-8")
    
    # Mock sys.argv
    original_argv = sys.argv
    try:
        sys.argv = ["svb2txt", str(input_file), "-o", str(output_file)]
        exit_code = main()
        
        assert exit_code == 0
        assert output_file.exists()
        
        output_content = output_file.read_text(encoding="utf-8")
        lines = output_content.strip().split("\n")
        
        assert len(lines) == 2
        assert "[00:00:01–00:00:03] First subtitle" in lines[0]
        assert "[00:00:04–00:00:06] Second subtitle" in lines[1]
        
    finally:
        sys.argv = original_argv


def test_main_with_merge(tmp_path):
    """Test main function with merge option."""
    sbv_content = """0:00:01.000,0:00:03.000
First

0:00:04.000,0:00:06.000
Second

0:00:07.000,0:00:09.000
Third
"""
    
    input_file = tmp_path / "test.sbv"
    output_file = tmp_path / "output.txt"
    
    input_file.write_text(sbv_content, encoding="utf-8")
    
    original_argv = sys.argv
    try:
        sys.argv = ["svb2txt", str(input_file), "-o", str(output_file), "-m", "10"]
        exit_code = main()
        
        assert exit_code == 0
        output_content = output_file.read_text(encoding="utf-8")
        
        # Should merge into one entry
        assert output_content.count("[") == 1
        assert "First Second Third" in output_content
        
    finally:
        sys.argv = original_argv

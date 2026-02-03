"""Tests for the CLI module."""

import json
from pathlib import Path

import pytest

from svb2json.cli import main


class TestCli:
    """Tests for the CLI."""

    def test_basic_conversion(self, tmp_path, capsys, monkeypatch):
        """Test basic SBV to JSON conversion."""
        sbv_content = """0:00:01.000,0:00:03.000
Hello World

0:00:04.000,0:00:06.000
Test subtitle

"""
        input_file = tmp_path / "test.sbv"
        input_file.write_text(sbv_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file)])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["text"] == "Hello World"
        assert result[1]["id"] == 2
        assert result[1]["text"] == "Test subtitle"

    def test_output_file(self, tmp_path, monkeypatch):
        """Test writing output to file."""
        sbv_content = """0:00:01.000,0:00:03.000
Hello World

"""
        input_file = tmp_path / "test.sbv"
        input_file.write_text(sbv_content, encoding="utf-8")
        output_file = tmp_path / "output.json"

        monkeypatch.setattr(
            "sys.argv", ["svb2json", str(input_file), "-o", str(output_file)]
        )
        exit_code = main()

        assert exit_code == 0
        assert output_file.exists()
        result = json.loads(output_file.read_text(encoding="utf-8"))
        assert len(result) == 1
        assert result[0]["text"] == "Hello World"

    def test_file_not_found(self, tmp_path, capsys, monkeypatch):
        """Test error when input file doesn't exist."""
        monkeypatch.setattr("sys.argv", ["svb2json", str(tmp_path / "nonexistent.sbv")])
        exit_code = main()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_seconds_flag(self, tmp_path, capsys, monkeypatch):
        """Test -s flag for seconds output."""
        sbv_content = """0:00:01.200,0:00:03.800
Test subtitle

"""
        input_file = tmp_path / "test.sbv"
        input_file.write_text(sbv_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file), "-s", "-f", "SS"])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert len(result) == 1
        assert result[0]["start"] == 1  # Rounded from 1200ms
        assert result[0]["end"] == 4    # Rounded from 3800ms

    def test_merge_flag(self, tmp_path, monkeypatch):
        """Test -m flag for merging subtitles."""
        sbv_content = """0:00:00.000,0:00:05.000
First subtitle

0:00:05.000,0:00:10.000
Second subtitle

"""
        input_file = tmp_path / "test.sbv"
        input_file.write_text(sbv_content, encoding="utf-8")
        output_file = tmp_path / "output.json"

        monkeypatch.setattr(
            "sys.argv", ["svb2json", str(input_file), "-s", "-m", "10", "-f", "SS", "-o", str(output_file)]
        )
        exit_code = main()

        assert exit_code == 0
        result = json.loads(output_file.read_text(encoding="utf-8"))
        assert len(result) == 1
        assert result[0]["text"] == "First subtitle Second subtitle"
        assert result[0]["start"] == 0
        assert result[0]["end"] == 10

    def test_merge_validation(self, tmp_path, capsys, monkeypatch):
        """Test that negative merge value is rejected."""
        sbv_content = """0:00:01.000,0:00:03.000
Test

"""
        input_file = tmp_path / "test.sbv"
        input_file.write_text(sbv_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file), "-m", "0"])
        exit_code = main()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "positive" in captured.err.lower()

    def test_multiline_text_joining(self, tmp_path, capsys, monkeypatch):
        """Test that multiline text is joined with spaces."""
        sbv_content = """0:00:01.000,0:00:03.000
Line one
Line two

"""
        input_file = tmp_path / "test.sbv"
        input_file.write_text(sbv_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file)])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result[0]["text"] == "Line one Line two"

    def test_simple_format_conversion(self, tmp_path, capsys, monkeypatch):
        """Test conversion of simple timestamp format."""
        simple_content = """0:00
First text
0:01
Second text
10:30
Third text"""
        input_file = tmp_path / "test.txt"
        input_file.write_text(simple_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file), "-f", "Mi"])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert len(result) == 3
        assert result[0]["id"] == 1
        assert result[0]["start"] == 0
        assert result[0]["end"] == 1000
        assert result[0]["text"] == "First text"

        assert result[1]["id"] == 2
        assert result[1]["start"] == 1000
        assert result[1]["end"] == 10 * 60 * 1000 + 30 * 1000
        assert result[1]["text"] == "Second text"

        assert result[2]["id"] == 3
        assert result[2]["start"] == 10 * 60 * 1000 + 30 * 1000
        assert result[2]["end"] == 10 * 60 * 1000 + 30 * 1000 + 5000
        assert result[2]["text"] == "Third text"

    def test_simple_format_with_seconds(self, tmp_path, capsys, monkeypatch):
        """Test simple format with -s flag."""
        simple_content = """0:01
Text 1
0:05
Text 2"""
        input_file = tmp_path / "test.txt"
        input_file.write_text(simple_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file), "-s", "-f", "SS"])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result[0]["start"] == 1
        assert result[0]["end"] == 5
        assert result[1]["start"] == 5
        assert result[1]["end"] == 10  # 5 + 5 default duration

    def test_simple_format_with_merge(self, tmp_path, monkeypatch):
        """Test simple format with -m flag."""
        simple_content = """0:00
Text 1
0:01
Text 2
0:02
Text 3"""
        input_file = tmp_path / "test.txt"
        input_file.write_text(simple_content, encoding="utf-8")
        output_file = tmp_path / "output.json"

        monkeypatch.setattr(
            "sys.argv", ["svb2json", str(input_file), "-s", "-m", "3", "-o", str(output_file)]
        )
        exit_code = main()

        assert exit_code == 0
        result = json.loads(output_file.read_text(encoding="utf-8"))
        # First two entries (1s each) should merge, third entry (5s with default) won't
        assert len(result) == 2
        assert result[0]["text"] == "Text 1 Text 2"

    def test_simple_format_with_formatting(self, tmp_path, capsys, monkeypatch):
        """Test simple format with -f flag."""
        simple_content = """0:00
Text 1
1:05
Text 2"""
        input_file = tmp_path / "test.txt"
        input_file.write_text(simple_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file), "-f", "HH:MM:SS"])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result[0]["start"] == "00:00:00"
        assert result[0]["end"] == "00:01:05"
        assert result[1]["start"] == "00:01:05"

    def test_simple_format_multiline_text(self, tmp_path, capsys, monkeypatch):
        """Test simple format with multiline text."""
        simple_content = """0:00
Line 1
Line 2
Line 3
0:05
Next text"""
        input_file = tmp_path / "test.txt"
        input_file.write_text(simple_content, encoding="utf-8")

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file)])
        exit_code = main()

        assert exit_code == 0
        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert result[0]["text"] == "Line 1 Line 2 Line 3"
        assert result[1]["text"] == "Next text"


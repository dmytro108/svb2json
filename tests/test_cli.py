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

        monkeypatch.setattr("sys.argv", ["svb2json", str(input_file), "-s"])
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
            "sys.argv", ["svb2json", str(input_file), "-s", "-m", "10", "-o", str(output_file)]
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


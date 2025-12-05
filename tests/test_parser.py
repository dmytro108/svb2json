"""Tests for the SBV parser module."""

import pytest

from svb2json.parser import parse_sbv, parse_timestamp


class TestParseTimestamp:
    """Tests for parse_timestamp function."""

    def test_simple_timestamp(self):
        """Test parsing a simple timestamp."""
        start, end = parse_timestamp("0:00:01.000,0:00:03.000")
        assert start == 1000
        assert end == 3000

    def test_timestamp_with_hours(self):
        """Test parsing a timestamp with hours."""
        start, end = parse_timestamp("1:30:45.500,2:15:30.250")
        assert start == (1 * 3600 + 30 * 60 + 45) * 1000 + 500
        assert end == (2 * 3600 + 15 * 60 + 30) * 1000 + 250

    def test_timestamp_with_whitespace(self):
        """Test parsing a timestamp with leading/trailing whitespace."""
        start, end = parse_timestamp("  0:00:01.000,0:00:03.000  ")
        assert start == 1000
        assert end == 3000

    def test_invalid_timestamp_raises(self):
        """Test that invalid timestamp raises ValueError."""
        with pytest.raises(ValueError):
            parse_timestamp("invalid")

    def test_invalid_format_raises(self):
        """Test that malformed timestamp raises ValueError."""
        with pytest.raises(ValueError):
            parse_timestamp("00:00:01.000-00:00:03.000")


class TestParseSbv:
    """Tests for parse_sbv function."""

    def test_single_entry(self):
        """Test parsing a single subtitle entry."""
        content = """0:00:01.000,0:00:03.000
Subtitle text 1

"""
        entries = parse_sbv(content)
        assert len(entries) == 1
        assert entries[0]["id"] == 1
        assert entries[0]["start"] == 1000
        assert entries[0]["end"] == 3000
        assert entries[0]["text"] == "Subtitle text 1"

    def test_multiple_entries(self):
        """Test parsing multiple subtitle entries."""
        content = """0:00:01.000,0:00:03.000
Subtitle text 1

0:00:04.000,0:00:06.000
Subtitle text 2

"""
        entries = parse_sbv(content)
        assert len(entries) == 2

        assert entries[0]["id"] == 1
        assert entries[0]["start"] == 1000
        assert entries[0]["end"] == 3000
        assert entries[0]["text"] == "Subtitle text 1"

        assert entries[1]["id"] == 2
        assert entries[1]["start"] == 4000
        assert entries[1]["end"] == 6000
        assert entries[1]["text"] == "Subtitle text 2"

    def test_multiline_text(self):
        """Test parsing subtitle with multiple lines of text."""
        content = """0:00:01.000,0:00:03.000
Line 1
Line 2

"""
        entries = parse_sbv(content)
        assert len(entries) == 1
        assert entries[0]["text"] == "Line 1\nLine 2"

    def test_empty_content(self):
        """Test parsing empty content."""
        entries = parse_sbv("")
        assert len(entries) == 0

    def test_content_with_leading_blank_lines(self):
        """Test parsing content with leading blank lines."""
        content = """

0:00:01.000,0:00:03.000
Subtitle text 1

"""
        entries = parse_sbv(content)
        assert len(entries) == 1
        assert entries[0]["text"] == "Subtitle text 1"

    def test_entries_without_trailing_blank_line(self):
        """Test parsing entries without trailing blank line."""
        content = """0:00:01.000,0:00:03.000
Subtitle text 1
0:00:04.000,0:00:06.000
Subtitle text 2"""
        entries = parse_sbv(content)
        assert len(entries) == 2
        assert entries[0]["text"] == "Subtitle text 1"
        assert entries[1]["text"] == "Subtitle text 2"

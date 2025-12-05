"""Tests for the SBV parser module."""

import pytest

from svb2json.parser import parse_sbv, parse_timestamp, merge_subtitles, merge_subtitles


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
        assert entries[0]["text"] == "Line 1 Line 2"

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

    def test_round_to_seconds(self):
        """Test parsing with round_to_seconds flag."""
        content = """0:00:01.200,0:00:03.800
Subtitle text 1

"""
        entries = parse_sbv(content, round_to_seconds=True)
        assert len(entries) == 1
        assert entries[0]["start"] == 1  # 1200ms rounds to 1s
        assert entries[0]["end"] == 4    # 3800ms rounds to 4s
        assert entries[0]["text"] == "Subtitle text 1"

    def test_milliseconds_default(self):
        """Test that milliseconds are returned by default."""
        content = """0:00:01.200,0:00:03.800
Subtitle text 1

"""
        entries = parse_sbv(content)
        assert len(entries) == 1
        assert entries[0]["start"] == 1200
        assert entries[0]["end"] == 3800


class TestMergeSubtitles:
    """Tests for merge_subtitles function."""

    def test_merge_basic(self):
        """Test basic merging of subtitles."""
        entries = [
            {"id": 1, "start": 0, "end": 5000, "text": "First"},
            {"id": 2, "start": 5000, "end": 10000, "text": "Second"},
        ]
        merged = merge_subtitles(entries, duration_seconds=10, use_seconds=False)
        assert len(merged) == 1
        assert merged[0]["start"] == 0
        assert merged[0]["end"] == 10000
        assert merged[0]["text"] == "First Second"

    def test_merge_with_seconds(self):
        """Test merging with seconds-based timestamps."""
        entries = [
            {"id": 1, "start": 0, "end": 5, "text": "First"},
            {"id": 2, "start": 5, "end": 10, "text": "Second"},
        ]
        merged = merge_subtitles(entries, duration_seconds=10, use_seconds=True)
        assert len(merged) == 1
        assert merged[0]["start"] == 0
        assert merged[0]["end"] == 10
        assert merged[0]["text"] == "First Second"

    def test_skip_long_subtitles(self):
        """Test that subtitles >= duration are not merged."""
        entries = [
            {"id": 1, "start": 0, "end": 10, "text": "Already long"},
            {"id": 2, "start": 10, "end": 15, "text": "Next"},
        ]
        merged = merge_subtitles(entries, duration_seconds=10, use_seconds=True)
        assert len(merged) == 2
        assert merged[0]["text"] == "Already long"
        assert merged[1]["text"] == "Next"

    def test_skip_threshold_subtitles(self):
        """Test that subtitles >= 2/3 duration threshold are not merged."""
        # For duration=12, threshold is round(2*12/3) = 8
        entries = [
            {"id": 1, "start": 0, "end": 8, "text": "At threshold"},
            {"id": 2, "start": 8, "end": 15, "text": "Next"},
        ]
        merged = merge_subtitles(entries, duration_seconds=12, use_seconds=True)
        assert len(merged) == 2
        assert merged[0]["text"] == "At threshold"
        assert merged[1]["text"] == "Next"

    def test_merge_multiple_short(self):
        """Test merging multiple short subtitles."""
        entries = [
            {"id": 1, "start": 0, "end": 3, "text": "One"},
            {"id": 2, "start": 3, "end": 6, "text": "Two"},
            {"id": 3, "start": 6, "end": 10, "text": "Three"},
        ]
        merged = merge_subtitles(entries, duration_seconds=10, use_seconds=True)
        assert len(merged) == 1
        assert merged[0]["text"] == "One Two Three"
        assert merged[0]["start"] == 0
        assert merged[0]["end"] == 10

    def test_renumber_ids(self):
        """Test that merged entries get renumbered IDs."""
        entries = [
            {"id": 5, "start": 0, "end": 10, "text": "First"},
            {"id": 10, "start": 10, "end": 15, "text": "Second"},
        ]
        merged = merge_subtitles(entries, duration_seconds=10, use_seconds=True)
        assert merged[0]["id"] == 1
        assert merged[1]["id"] == 2

    def test_empty_entries(self):
        """Test merging empty list."""
        merged = merge_subtitles([], duration_seconds=10, use_seconds=True)
        assert len(merged) == 0

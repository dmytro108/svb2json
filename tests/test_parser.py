"""Tests for the SBV parser module."""

import pytest

from svb2json.parser import (
    parse_sbv,
    parse_timestamp,
    merge_subtitles,
    detect_format,
    parse_simple_timestamp,
    parse_simple,
    parse_subtitles,
)


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


class TestDetectFormat:
    """Tests for detect_format function."""

    def test_detect_sbv_format(self):
        """Test detecting SBV format."""
        content = "0:00:01.000,0:00:03.000\nText"
        assert detect_format(content) == "sbv"

    def test_detect_simple_format(self):
        """Test detecting simple format."""
        content = "0:00\nText"
        assert detect_format(content) == "simple"

    def test_detect_with_leading_blank_lines(self):
        """Test detection with leading blank lines."""
        content = "\n\n0:00\nText"
        assert detect_format(content) == "simple"

    def test_detect_sbv_with_blank_lines(self):
        """Test detecting SBV with blank lines."""
        content = "\n\n0:00:01.000,0:00:03.000\nText"
        assert detect_format(content) == "sbv"

    def test_invalid_content_raises(self):
        """Test that invalid content raises ValueError."""
        with pytest.raises(ValueError, match="Could not detect subtitle format"):
            detect_format("Just some random text")

    def test_empty_content_raises(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Could not detect subtitle format"):
            detect_format("")

    def test_only_whitespace_raises(self):
        """Test that only whitespace raises ValueError."""
        with pytest.raises(ValueError, match="Could not detect subtitle format"):
            detect_format("\n\n   \n")


class TestParseSimpleTimestamp:
    """Tests for parse_simple_timestamp function."""

    def test_zero_timestamp(self):
        """Test parsing 0:00."""
        ms = parse_simple_timestamp("0:00")
        assert ms == 0

    def test_simple_timestamp(self):
        """Test parsing 0:01."""
        ms = parse_simple_timestamp("0:01")
        assert ms == 1000

    def test_minutes_timestamp(self):
        """Test parsing 10:30."""
        ms = parse_simple_timestamp("10:30")
        assert ms == (10 * 60 + 30) * 1000

    def test_large_minutes(self):
        """Test parsing 120:30."""
        ms = parse_simple_timestamp("120:30")
        assert ms == (120 * 60 + 30) * 1000

    def test_with_whitespace(self):
        """Test parsing with leading/trailing whitespace."""
        ms = parse_simple_timestamp("  10:30  ")
        assert ms == (10 * 60 + 30) * 1000

    def test_invalid_format_raises(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid simple timestamp format"):
            parse_simple_timestamp("1:2")  # seconds must be 2 digits

    def test_invalid_format_with_milliseconds_raises(self):
        """Test that SBV-style timestamp raises ValueError."""
        with pytest.raises(ValueError, match="Invalid simple timestamp format"):
            parse_simple_timestamp("0:00:01.000")

    def test_negative_timestamp_raises(self):
        """Test that negative timestamp raises ValueError."""
        with pytest.raises(ValueError, match="Invalid simple timestamp format"):
            parse_simple_timestamp("-1:00")


class TestParseSimple:
    """Tests for parse_simple function."""

    def test_single_entry(self):
        """Test parsing a single entry."""
        content = """0:00
Text line 1"""
        entries = parse_simple(content)
        assert len(entries) == 1
        assert entries[0]["id"] == 1
        assert entries[0]["start"] == 0
        assert entries[0]["end"] == 5000  # default duration
        assert entries[0]["text"] == "Text line 1"

    def test_multiple_entries(self):
        """Test parsing multiple entries with end time calculation."""
        content = """0:00
First text
0:01
Second text
10:30
Third text"""
        entries = parse_simple(content)
        assert len(entries) == 3

        assert entries[0]["id"] == 1
        assert entries[0]["start"] == 0
        assert entries[0]["end"] == 1000
        assert entries[0]["text"] == "First text"

        assert entries[1]["id"] == 2
        assert entries[1]["start"] == 1000
        assert entries[1]["end"] == 10 * 60 * 1000 + 30 * 1000
        assert entries[1]["text"] == "Second text"

        assert entries[2]["id"] == 3
        assert entries[2]["start"] == 10 * 60 * 1000 + 30 * 1000
        assert entries[2]["end"] == 10 * 60 * 1000 + 30 * 1000 + 5000
        assert entries[2]["text"] == "Third text"

    def test_multiline_text(self):
        """Test that multiline text is joined with spaces."""
        content = """0:00
Line 1
Line 2
Line 3
0:05
Next text"""
        entries = parse_simple(content)
        assert len(entries) == 2
        assert entries[0]["text"] == "Line 1 Line 2 Line 3"
        assert entries[1]["text"] == "Next text"

    def test_empty_text_after_timestamp(self):
        """Test handling entry with no text."""
        content = """0:00

0:05
Some text"""
        entries = parse_simple(content)
        assert len(entries) == 2
        assert entries[0]["text"] == ""
        assert entries[1]["text"] == "Some text"

    def test_leading_blank_lines(self):
        """Test handling leading blank lines."""
        content = """

0:00
Text"""
        entries = parse_simple(content)
        assert len(entries) == 1
        assert entries[0]["text"] == "Text"

    def test_text_before_first_timestamp_ignored(self):
        """Test that text before first timestamp is ignored."""
        content = """Random text
More random text
0:00
Real text"""
        entries = parse_simple(content)
        assert len(entries) == 1
        assert entries[0]["text"] == "Real text"

    def test_round_to_seconds(self):
        """Test parsing with round_to_seconds flag."""
        content = """0:01
Text 1
0:03
Text 2"""
        entries = parse_simple(content, round_to_seconds=True)
        assert entries[0]["start"] == 1
        assert entries[0]["end"] == 3
        assert entries[1]["start"] == 3
        assert entries[1]["end"] == 8  # 3 + 5 default duration

    def test_custom_default_duration(self):
        """Test using custom default duration for last entry."""
        content = """0:00
Only entry"""
        entries = parse_simple(content, default_duration_ms=10000)
        assert entries[0]["end"] == 10000

    def test_empty_content_raises(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse empty content"):
            parse_simple("")

    def test_only_whitespace_raises(self):
        """Test that only whitespace raises ValueError."""
        with pytest.raises(ValueError, match="Cannot parse empty content"):
            parse_simple("\n\n   \n")

    def test_blank_lines_between_entries(self):
        """Test handling blank lines between entries."""
        content = """0:00
Text 1


0:05
Text 2"""
        entries = parse_simple(content)
        assert len(entries) == 2
        assert entries[0]["text"] == "Text 1"
        assert entries[1]["text"] == "Text 2"


class TestParseSubtitles:
    """Tests for parse_subtitles unified parser."""

    def test_auto_detect_sbv(self):
        """Test auto-detection of SBV format."""
        content = """0:00:01.000,0:00:03.000
Subtitle text"""
        entries = parse_subtitles(content)
        assert len(entries) == 1
        assert entries[0]["start"] == 1000
        assert entries[0]["end"] == 3000

    def test_auto_detect_simple(self):
        """Test auto-detection of simple format."""
        content = """0:00
Text 1
0:05
Text 2"""
        entries = parse_subtitles(content)
        assert len(entries) == 2
        assert entries[0]["end"] == 5000
        assert entries[1]["end"] == 10000  # 5s + 5s default

    def test_format_hint_sbv(self):
        """Test using format hint to force SBV parsing."""
        content = """0:00:01.000,0:00:03.000
Text"""
        entries = parse_subtitles(content, format_hint="sbv")
        assert len(entries) == 1
        assert entries[0]["start"] == 1000

    def test_format_hint_simple(self):
        """Test using format hint to force simple parsing."""
        content = """0:00
Text"""
        entries = parse_subtitles(content, format_hint="simple")
        assert len(entries) == 1
        assert entries[0]["start"] == 0

    def test_round_to_seconds_sbv(self):
        """Test round_to_seconds with SBV format."""
        content = """0:00:01.500,0:00:03.800
Text"""
        entries = parse_subtitles(content, round_to_seconds=True)
        assert entries[0]["start"] == 2
        assert entries[0]["end"] == 4

    def test_round_to_seconds_simple(self):
        """Test round_to_seconds with simple format."""
        content = """0:01
Text 1
0:05
Text 2"""
        entries = parse_subtitles(content, round_to_seconds=True)
        assert entries[0]["start"] == 1
        assert entries[0]["end"] == 5

    def test_custom_default_duration(self):
        """Test custom default_duration_ms for simple format."""
        content = """0:00
Only entry"""
        entries = parse_subtitles(content, default_duration_ms=10000)
        assert entries[0]["end"] == 10000

    def test_invalid_format_hint_raises(self):
        """Test that invalid format hint raises ValueError."""
        content = """0:00
Text"""
        with pytest.raises(ValueError, match="Unknown format"):
            parse_subtitles(content, format_hint="invalid")

    def test_integration_with_merge(self):
        """Test that parse_subtitles works with merge_subtitles."""
        content = """0:00
Text 1
0:01
Text 2
0:02
Text 3
0:03
Text 4"""
        entries = parse_subtitles(content)
        # Entries: 0-1s, 1-2s, 2-3s, 3-8s (last gets 5s default)
        # Merge with 3s duration: first three entries (each 1s) should merge
        # Last entry is 5s (>= threshold 2s) so won't merge
        merged = merge_subtitles(entries, duration_seconds=3, use_seconds=False)
        assert len(merged) == 2
        assert merged[0]["text"] == "Text 1 Text 2 Text 3"
        assert merged[0]["start"] == 0
        assert merged[0]["end"] == 3000
        assert merged[1]["text"] == "Text 4"

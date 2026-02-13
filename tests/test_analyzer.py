"""Tests for the timing anomaly analyzer."""

import pytest
from svb2json.analyzer import (
    detect_gaps,
    detect_short_phrases,
    detect_silence,
    analyze_subtitles,
    generate_statistics,
)


class TestDetectGaps:
    """Test gap detection between subtitles."""

    def test_no_gaps(self):
        """Test subtitles with no gaps between them."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 1000, "end": 2000, "text": "Second"},
            {"id": 3, "start": 2000, "end": 3000, "text": "Third"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 0

    def test_single_gap(self):
        """Test detection of a single gap."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 2500, "end": 3500, "text": "Second"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 1
        assert gaps[0]["type"] == "gap"
        assert gaps[0]["start_ms"] == 1000
        assert gaps[0]["end_ms"] == 2500
        assert gaps[0]["duration_ms"] == 1500
        assert gaps[0]["severity"] == "low"

    def test_multiple_gaps(self):
        """Test detection of multiple gaps."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 2200, "end": 3000, "text": "Second"},
            {"id": 3, "start": 5500, "end": 6000, "text": "Third"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 2
        assert gaps[0]["duration_ms"] == 1200
        assert gaps[1]["duration_ms"] == 2500

    def test_gap_severity_levels(self):
        """Test correct severity assignment for different gap durations."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 2500, "end": 3000, "text": "Second (low)"},
            {"id": 3, "start": 5500, "end": 6000, "text": "Third (medium)"},
            {"id": 4, "start": 11500, "end": 12000, "text": "Fourth (high)"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 3
        assert gaps[0]["severity"] == "low"  # 1.5s gap
        assert gaps[1]["severity"] == "medium"  # 2.5s gap
        assert gaps[2]["severity"] == "high"  # 5.5s gap

    def test_small_gaps_below_threshold(self):
        """Test that gaps below threshold are not reported."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 1500, "end": 2500, "text": "Second"},
            {"id": 3, "start": 3000, "end": 4000, "text": "Third"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 0

    def test_custom_threshold(self):
        """Test detection with custom gap threshold."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 1300, "end": 2000, "text": "Second"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=200)
        assert len(gaps) == 1
        assert gaps[0]["duration_ms"] == 300

    def test_gap_context_information(self):
        """Test that gap includes context about surrounding subtitles."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First subtitle text"},
            {"id": 2, "start": 2500, "end": 3500, "text": "Second subtitle text"},
        ]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert gaps[0]["context"]["previous_subtitle_id"] == 1
        assert gaps[0]["context"]["next_subtitle_id"] == 2
        assert "First subtitle" in gaps[0]["context"]["previous_text"]
        assert "Second subtitle" in gaps[0]["context"]["next_text"]

    def test_single_subtitle(self):
        """Test that single subtitle produces no gaps."""
        subtitles = [{"id": 1, "start": 0, "end": 1000, "text": "Only one"}]
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 0

    def test_empty_subtitles(self):
        """Test that empty subtitle list produces no gaps."""
        subtitles = []
        gaps = detect_gaps(subtitles, gap_threshold_ms=1000)
        assert len(gaps) == 0


class TestDetectShortPhrases:
    """Test detection of too-short subtitle phrases."""

    def test_no_short_phrases(self):
        """Test subtitles with normal durations."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "Normal"},
            {"id": 2, "start": 1000, "end": 2500, "text": "Also normal"},
        ]
        short = detect_short_phrases(subtitles, min_phrase_ms=300)
        assert len(short) == 0

    def test_single_short_phrase(self):
        """Test detection of a single short phrase."""
        subtitles = [
            {"id": 1, "start": 0, "end": 200, "text": "Too short"},
            {"id": 2, "start": 1000, "end": 2000, "text": "Normal"},
        ]
        short = detect_short_phrases(subtitles, min_phrase_ms=300)
        assert len(short) == 1
        assert short[0]["type"] == "short_phrase"
        assert short[0]["duration_ms"] == 200
        assert short[0]["severity"] == "low"

    def test_multiple_short_phrases(self):
        """Test detection of multiple short phrases."""
        subtitles = [
            {"id": 1, "start": 0, "end": 50, "text": "Very short"},
            {"id": 2, "start": 1000, "end": 1150, "text": "Also short"},
            {"id": 3, "start": 2000, "end": 2250, "text": "Short too"},
        ]
        short = detect_short_phrases(subtitles, min_phrase_ms=300)
        assert len(short) == 3

    def test_severity_levels(self):
        """Test correct severity assignment for different phrase durations."""
        subtitles = [
            {"id": 1, "start": 0, "end": 50, "text": "High severity"},
            {"id": 2, "start": 1000, "end": 1150, "text": "Medium severity"},
            {"id": 3, "start": 2000, "end": 2250, "text": "Low severity"},
        ]
        short = detect_short_phrases(subtitles, min_phrase_ms=300)
        assert short[0]["severity"] == "high"  # 50ms < 100ms
        assert short[1]["severity"] == "medium"  # 150ms is 100-200ms
        assert short[2]["severity"] == "low"  # 250ms is 200-300ms

    def test_custom_threshold(self):
        """Test detection with custom minimum phrase duration."""
        subtitles = [
            {"id": 1, "start": 0, "end": 600, "text": "Normal at 300, short at 800"},
        ]
        short = detect_short_phrases(subtitles, min_phrase_ms=800)
        assert len(short) == 1

    def test_phrase_context(self):
        """Test that short phrase includes context information."""
        subtitles = [
            {"id": 1, "start": 0, "end": 100, "text": "Short text"},
        ]
        short = detect_short_phrases(subtitles, min_phrase_ms=300)
        assert short[0]["context"]["subtitle_id"] == 1
        assert short[0]["context"]["text"] == "Short text"
        assert short[0]["context"]["text_length"] == 10

    def test_empty_subtitles(self):
        """Test that empty subtitle list produces no short phrases."""
        subtitles = []
        short = detect_short_phrases(subtitles, min_phrase_ms=300)
        assert len(short) == 0


class TestDetectSilence:
    """Test detection of silence periods (long gaps)."""

    def test_no_silence(self):
        """Test subtitles without silence periods."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 2000, "end": 3000, "text": "Second"},
        ]
        silence = detect_silence(subtitles, silence_threshold_ms=3000)
        assert len(silence) == 0

    def test_single_silence(self):
        """Test detection of a single silence period."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 5000, "end": 6000, "text": "Second"},
        ]
        silence = detect_silence(subtitles, silence_threshold_ms=3000)
        assert len(silence) == 1
        assert silence[0]["type"] == "silence"
        assert silence[0]["start_ms"] == 1000
        assert silence[0]["end_ms"] == 5000
        assert silence[0]["duration_ms"] == 4000
        assert silence[0]["severity"] == "high"

    def test_multiple_silence_periods(self):
        """Test detection of multiple silence periods."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 5000, "end": 6000, "text": "Second"},
            {"id": 3, "start": 10000, "end": 11000, "text": "Third"},
        ]
        silence = detect_silence(subtitles, silence_threshold_ms=3000)
        assert len(silence) == 2

    def test_silence_context(self):
        """Test that silence includes context information."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 5000, "end": 6000, "text": "Second"},
        ]
        silence = detect_silence(subtitles, silence_threshold_ms=3000)
        assert silence[0]["context"]["previous_subtitle_id"] == 1
        assert silence[0]["context"]["next_subtitle_id"] == 2
        assert silence[0]["context"]["gap_seconds"] == 4.0

    def test_custom_threshold(self):
        """Test detection with custom silence threshold."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 3000, "end": 4000, "text": "Second"},
        ]
        silence = detect_silence(subtitles, silence_threshold_ms=1500)
        assert len(silence) == 1

    def test_single_subtitle(self):
        """Test that single subtitle produces no silence."""
        subtitles = [{"id": 1, "start": 0, "end": 1000, "text": "Only one"}]
        silence = detect_silence(subtitles, silence_threshold_ms=3000)
        assert len(silence) == 0


class TestAnalyzeSubtitles:
    """Test comprehensive subtitle analysis."""

    def test_combined_anomaly_detection(self):
        """Test that all anomaly types are detected together."""
        subtitles = [
            {"id": 1, "start": 0, "end": 100, "text": "Too short"},
            {"id": 2, "start": 1500, "end": 2500, "text": "Normal"},
            {"id": 3, "start": 6000, "end": 7000, "text": "After silence"},
        ]
        anomalies = analyze_subtitles(
            subtitles,
            gap_threshold_ms=1000,
            min_phrase_ms=300,
            silence_threshold_ms=3000
        )
        # Should detect: short phrase, gap, silence, gap
        assert len(anomalies) >= 2  # At least short phrase and silence

    def test_sorted_by_timestamp(self):
        """Test that anomalies are sorted by start timestamp."""
        subtitles = [
            {"id": 1, "start": 0, "end": 100, "text": "Short"},
            {"id": 2, "start": 2000, "end": 3000, "text": "Normal"},
            {"id": 3, "start": 3100, "end": 3150, "text": "Also short"},
        ]
        anomalies = analyze_subtitles(subtitles, gap_threshold_ms=1000, min_phrase_ms=300)
        # Verify chronological order
        for i in range(len(anomalies) - 1):
            assert anomalies[i]["start_ms"] <= anomalies[i + 1]["start_ms"]

    def test_custom_thresholds(self):
        """Test analysis with custom threshold values."""
        subtitles = [
            {"id": 1, "start": 0, "end": 500, "text": "First"},
            {"id": 2, "start": 2000, "end": 3000, "text": "Second"},
        ]
        anomalies = analyze_subtitles(
            subtitles,
            gap_threshold_ms=500,
            min_phrase_ms=600,
            silence_threshold_ms=1000
        )
        # Should detect gap and short phrase and silence with these thresholds
        assert len(anomalies) >= 2

    def test_no_anomalies(self):
        """Test subtitles with no anomalies."""
        subtitles = [
            {"id": 1, "start": 0, "end": 1000, "text": "First"},
            {"id": 2, "start": 1000, "end": 2000, "text": "Second"},
            {"id": 3, "start": 2000, "end": 3000, "text": "Third"},
        ]
        anomalies = analyze_subtitles(subtitles)
        assert len(anomalies) == 0

    def test_empty_subtitles(self):
        """Test analysis with empty subtitle list."""
        anomalies = analyze_subtitles([])
        assert len(anomalies) == 0


class TestGenerateStatistics:
    """Test statistics generation from anomalies."""

    def test_empty_anomalies(self):
        """Test statistics with no anomalies."""
        stats = generate_statistics([])
        assert stats["total_anomalies"] == 0
        assert stats["by_type"]["gap"] == 0
        assert stats["by_type"]["short_phrase"] == 0
        assert stats["by_type"]["silence"] == 0

    def test_count_by_type(self):
        """Test counting anomalies by type."""
        anomalies = [
            {"type": "gap", "start_ms": 0, "end_ms": 1000, "duration_ms": 1000, "severity": "low", "context": {}},
            {"type": "gap", "start_ms": 2000, "end_ms": 3000, "duration_ms": 1000, "severity": "medium", "context": {}},
            {"type": "short_phrase", "start_ms": 4000, "end_ms": 4100, "duration_ms": 100, "severity": "high", "context": {}},
            {"type": "silence", "start_ms": 5000, "end_ms": 9000, "duration_ms": 4000, "severity": "high", "context": {}},
        ]
        stats = generate_statistics(anomalies)
        assert stats["total_anomalies"] == 4
        assert stats["by_type"]["gap"] == 2
        assert stats["by_type"]["short_phrase"] == 1
        assert stats["by_type"]["silence"] == 1

    def test_count_by_severity(self):
        """Test counting anomalies by severity."""
        anomalies = [
            {"type": "gap", "start_ms": 0, "end_ms": 1000, "duration_ms": 1000, "severity": "low", "context": {}},
            {"type": "gap", "start_ms": 2000, "end_ms": 3000, "duration_ms": 1000, "severity": "medium", "context": {}},
            {"type": "short_phrase", "start_ms": 4000, "end_ms": 4100, "duration_ms": 100, "severity": "high", "context": {}},
            {"type": "silence", "start_ms": 5000, "end_ms": 9000, "duration_ms": 4000, "severity": "high", "context": {}},
        ]
        stats = generate_statistics(anomalies)
        assert stats["by_severity"]["low"] == 1
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_severity"]["high"] == 2

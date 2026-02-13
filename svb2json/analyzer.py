"""Timing anomaly detection for SBV subtitle files."""
from typing import List, Literal, TypedDict
from svb2json.parser import SubtitleEntry


class TimingAnomaly(TypedDict):
    """Represents a detected timing anomaly in subtitles."""
    type: Literal["gap", "short_phrase", "silence"]
    start_ms: int
    end_ms: int
    duration_ms: int
    severity: Literal["low", "medium", "high"]
    context: dict  # Additional context about the anomaly


def detect_gaps(
    subtitles: List[SubtitleEntry],
    gap_threshold_ms: int = 1000
) -> List[TimingAnomaly]:
    """
    Detect gaps/pauses between consecutive subtitles.
    
    Args:
        subtitles: List of parsed subtitle entries
        gap_threshold_ms: Minimum gap duration in milliseconds to report (default: 1000ms = 1s)
    
    Returns:
        List of gap anomalies with timing and context information
    """
    gaps = []
    
    for i in range(len(subtitles) - 1):
        current = subtitles[i]
        next_subtitle = subtitles[i + 1]
        
        # Calculate gap between end of current and start of next
        gap_duration = next_subtitle["start"] - current["end"]
        
        if gap_duration >= gap_threshold_ms:
            # Determine severity based on gap duration
            if gap_duration >= 5000:  # 5+ seconds
                severity = "high"
            elif gap_duration >= 2000:  # 2-5 seconds
                severity = "medium"
            else:  # 1-2 seconds
                severity = "low"
            
            gaps.append({
                "type": "gap",
                "start_ms": current["end"],
                "end_ms": next_subtitle["start"],
                "duration_ms": gap_duration,
                "severity": severity,
                "context": {
                    "previous_subtitle_id": current["id"],
                    "next_subtitle_id": next_subtitle["id"],
                    "previous_text": current["text"][:50],  # First 50 chars
                    "next_text": next_subtitle["text"][:50]
                }
            })
    
    return gaps


def detect_short_phrases(
    subtitles: List[SubtitleEntry],
    min_phrase_ms: int = 300
) -> List[TimingAnomaly]:
    """
    Detect subtitles that are too short in duration.
    
    Args:
        subtitles: List of parsed subtitle entries
        min_phrase_ms: Minimum acceptable phrase duration in milliseconds (default: 300ms)
    
    Returns:
        List of short phrase anomalies
    """
    short_phrases = []
    
    for subtitle in subtitles:
        duration = subtitle["end"] - subtitle["start"]
        
        if duration < min_phrase_ms:
            # Determine severity based on how short it is
            if duration < 100:  # Less than 0.1 seconds
                severity = "high"
            elif duration < 200:  # 0.1-0.2 seconds
                severity = "medium"
            else:  # 0.2-0.3 seconds
                severity = "low"
            
            short_phrases.append({
                "type": "short_phrase",
                "start_ms": subtitle["start"],
                "end_ms": subtitle["end"],
                "duration_ms": duration,
                "severity": severity,
                "context": {
                    "subtitle_id": subtitle["id"],
                    "text": subtitle["text"],
                    "text_length": len(subtitle["text"])
                }
            })
    
    return short_phrases


def detect_silence(
    subtitles: List[SubtitleEntry],
    silence_threshold_ms: int = 3000
) -> List[TimingAnomaly]:
    """
    Detect periods of silence (long gaps with no subtitles).
    
    Args:
        subtitles: List of parsed subtitle entries
        silence_threshold_ms: Minimum duration to consider as silence (default: 3000ms = 3s)
    
    Returns:
        List of silence anomalies
    """
    silence_periods = []
    
    for i in range(len(subtitles) - 1):
        current = subtitles[i]
        next_subtitle = subtitles[i + 1]
        
        gap_duration = next_subtitle["start"] - current["end"]
        
        if gap_duration >= silence_threshold_ms:
            silence_periods.append({
                "type": "silence",
                "start_ms": current["end"],
                "end_ms": next_subtitle["start"],
                "duration_ms": gap_duration,
                "severity": "high",  # Silence is always high severity
                "context": {
                    "previous_subtitle_id": current["id"],
                    "next_subtitle_id": next_subtitle["id"],
                    "gap_seconds": round(gap_duration / 1000, 2)
                }
            })
    
    return silence_periods


def analyze_subtitles(
    subtitles: List[SubtitleEntry],
    gap_threshold_ms: int = 1000,
    min_phrase_ms: int = 300,
    silence_threshold_ms: int = 3000
) -> List[TimingAnomaly]:
    """
    Perform comprehensive timing analysis on subtitle entries.
    
    Args:
        subtitles: List of parsed subtitle entries
        gap_threshold_ms: Minimum gap duration to report (default: 1000ms)
        min_phrase_ms: Minimum acceptable phrase duration (default: 300ms)
        silence_threshold_ms: Minimum duration for silence detection (default: 3000ms)
    
    Returns:
        List of all detected anomalies, sorted by start timestamp
    """
    all_anomalies = []
    
    # Detect all anomaly types
    all_anomalies.extend(detect_gaps(subtitles, gap_threshold_ms))
    all_anomalies.extend(detect_short_phrases(subtitles, min_phrase_ms))
    all_anomalies.extend(detect_silence(subtitles, silence_threshold_ms))
    
    # Sort by start timestamp
    all_anomalies.sort(key=lambda x: x["start_ms"])
    
    return all_anomalies


def generate_statistics(anomalies: List[TimingAnomaly]) -> dict:
    """
    Generate summary statistics for detected anomalies.
    
    Args:
        anomalies: List of detected timing anomalies
    
    Returns:
        Dictionary containing counts and statistics by type and severity
    """
    stats = {
        "total_anomalies": len(anomalies),
        "by_type": {
            "gap": 0,
            "short_phrase": 0,
            "silence": 0
        },
        "by_severity": {
            "low": 0,
            "medium": 0,
            "high": 0
        }
    }
    
    for anomaly in anomalies:
        stats["by_type"][anomaly["type"]] += 1
        stats["by_severity"][anomaly["severity"]] += 1
    
    return stats

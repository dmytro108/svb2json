"""SBV subtitle file parser."""

import re
from typing import List, TypedDict, Union


class SubtitleEntry(TypedDict):
    """Represents a single subtitle entry."""

    id: int
    start: int
    end: int
    text: str


# Regex pattern for SBV timestamp format: h:mm:ss.mmm,h:mm:ss.mmm
TIMESTAMP_PATTERN = re.compile(
    r"^(\d+):(\d{2}):(\d{2})\.(\d{3}),(\d+):(\d{2}):(\d{2})\.(\d{3})$"
)

# Regex pattern for simple timestamp format: M:SS (minutes:seconds, minutes can be any length)
SIMPLE_TIMESTAMP_PATTERN = re.compile(r"^(\d+):(\d{2})$")


def parse_timestamp(timestamp: str) -> tuple[int, int]:
    """Parse an SBV timestamp line and return start/end times in milliseconds.

    Args:
        timestamp: Timestamp string in format "h:mm:ss.mmm,h:mm:ss.mmm"

    Returns:
        Tuple of (start_ms, end_ms) times in milliseconds

    Raises:
        ValueError: If timestamp format is invalid
    """
    match = TIMESTAMP_PATTERN.match(timestamp.strip())
    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}")

    groups = match.groups()
    start_h, start_m, start_s, start_ms = map(int, groups[:4])
    end_h, end_m, end_s, end_ms = map(int, groups[4:])

    start_total_ms = (start_h * 3600 + start_m * 60 + start_s) * 1000 + start_ms
    end_total_ms = (end_h * 3600 + end_m * 60 + end_s) * 1000 + end_ms

    return start_total_ms, end_total_ms


def format_timestamp(ms: int, format_type: str) -> Union[str, int]:
    """Format a timestamp in milliseconds to the specified format.

    Args:
        ms: Timestamp in milliseconds
        format_type: One of "HH:MM:SS.Mi", "HH:MM:SS", "HH:MM", "SS", "MM", "Mi"

    Returns:
        Formatted timestamp as string or integer
    """
    if format_type == "Mi":
        return ms
    
    if format_type == "SS":
        return round(ms / 1000)
    
    if format_type == "MM":
        return round(ms / 60000)
    
    # For time formats, calculate hours, minutes, seconds, milliseconds
    total_seconds = ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int(ms % 1000)
    
    if format_type == "HH:MM":
        # Round to nearest minute
        total_minutes = round(ms / 60000)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    if format_type == "HH:MM:SS":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    if format_type == "HH:MM:SS.Mi":
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    raise ValueError(f"Invalid format type: {format_type}")


def parse_sbv(content: str, round_to_seconds: bool = False) -> List[SubtitleEntry]:
    """Parse SBV subtitle content and return a list of subtitle entries.

    Args:
        content: The full content of an SBV file
        round_to_seconds: If True, round timestamps to whole seconds and convert to seconds

    Returns:
        List of SubtitleEntry dictionaries
    """
    entries: List[SubtitleEntry] = []
    lines = content.split("\n")
    entry_id = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this line is a timestamp
        if TIMESTAMP_PATTERN.match(line):
            entry_id += 1
            start_ms, end_ms = parse_timestamp(line)

            # Collect text lines until we hit an empty line or another timestamp
            text_lines = []
            i += 1
            while i < len(lines):
                text_line = lines[i]
                stripped = text_line.strip()
                # Stop if we hit an empty line or another timestamp
                if not stripped or TIMESTAMP_PATTERN.match(stripped):
                    break
                text_lines.append(text_line.strip())
                i += 1

            text = " ".join(text_lines).strip()

            # Convert to seconds if requested
            if round_to_seconds:
                start_time = round(start_ms / 1000)
                end_time = round(end_ms / 1000)
            else:
                start_time = start_ms
                end_time = end_ms

            entries.append(
                {
                    "id": entry_id,
                    "start": start_time,
                    "end": end_time,
                    "text": text,
                }
            )
        else:
            # Skip non-timestamp lines that aren't part of an entry
            i += 1

    return entries


def merge_subtitles(
    entries: List[SubtitleEntry], duration_seconds: int, use_seconds: bool = False
) -> List[SubtitleEntry]:
    """Merge subtitle entries into timeframes of specified duration.

    Only merges subtitles that are shorter than round(2*duration/3). Skips merging
    if a subtitle already lasts duration_seconds or more.

    Args:
        entries: List of subtitle entries to merge
        duration_seconds: Duration in seconds for each merged timeframe
        use_seconds: Whether timestamps are in seconds (True) or milliseconds (False)

    Returns:
        List of merged subtitle entries with renumbered IDs
    """
    if not entries:
        return []

    merged: List[SubtitleEntry] = []
    
    # Convert duration to the appropriate unit
    if use_seconds:
        duration = duration_seconds
        min_duration_threshold = round(2 * duration_seconds / 3)
    else:
        duration = duration_seconds * 1000
        min_duration_threshold = round(2 * duration_seconds * 1000 / 3)

    i = 0
    while i < len(entries):
        entry = entries[i]
        entry_duration = entry["end"] - entry["start"]
        
        # If this subtitle already lasts >= NN seconds, don't merge it
        if entry_duration >= duration:
            merged.append(
                {
                    "id": len(merged) + 1,
                    "start": entry["start"],
                    "end": entry["end"],
                    "text": entry["text"],
                }
            )
            i += 1
            continue
        
        # Only merge if current subtitle is short enough
        if entry_duration >= min_duration_threshold:
            merged.append(
                {
                    "id": len(merged) + 1,
                    "start": entry["start"],
                    "end": entry["end"],
                    "text": entry["text"],
                }
            )
            i += 1
            continue
        
        # Start merging process
        current_group_texts = [entry["text"]]
        current_group_start = entry["start"]
        target_end_time = current_group_start + duration
        i += 1
        
        # Look for next entries to merge
        while i < len(entries):
            next_entry = entries[i]
            next_duration = next_entry["end"] - next_entry["start"]
            
            # Don't merge if next subtitle is too long
            if next_duration >= min_duration_threshold:
                # Create merged entry with what we've collected so far
                if current_group_texts:
                    last_end = entries[i - 1]["end"]
                    merged.append(
                        {
                            "id": len(merged) + 1,
                            "start": current_group_start,
                            "end": last_end,
                            "text": " ".join(current_group_texts),
                        }
                    )
                break
            
            # If this entry completes or exceeds the timeframe, include it and stop
            if next_entry["end"] >= target_end_time:
                current_group_texts.append(next_entry["text"])
                i += 1
                
                # Create merged entry
                merged.append(
                    {
                        "id": len(merged) + 1,
                        "start": current_group_start,
                        "end": next_entry["end"],
                        "text": " ".join(current_group_texts),
                    }
                )
                break
            else:
                # Add to current group and continue
                current_group_texts.append(next_entry["text"])
                i += 1
        else:
            # Reached end of entries without completing timeframe
            # Create merged entry with what we have
            last_end = entries[i - 1]["end"]
            merged.append(
                {
                    "id": len(merged) + 1,
                    "start": current_group_start,
                    "end": last_end,
                    "text": " ".join(current_group_texts),
                }
            )

    return merged


def detect_format(content: str) -> str:
    """Detect the subtitle format from content.

    Args:
        content: The subtitle file content

    Returns:
        "sbv" for SBV format, "simple" for simple format

    Raises:
        ValueError: If format cannot be detected
    """
    lines = content.strip().split("\n")

    # Find first non-empty line
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if it's SBV format
        if TIMESTAMP_PATTERN.match(stripped):
            return "sbv"

        # Check if it's simple format
        if SIMPLE_TIMESTAMP_PATTERN.match(stripped):
            return "simple"

        # If we found a non-empty line that's not a timestamp, format is unclear
        break

    raise ValueError("Could not detect subtitle format - no valid timestamp found")


def parse_simple_timestamp(timestamp: str) -> int:
    """Parse a simple timestamp and return time in milliseconds.

    Args:
        timestamp: Timestamp string in format "m:ss" or "mm:ss"

    Returns:
        Time in milliseconds

    Raises:
        ValueError: If timestamp format is invalid
    """
    match = SIMPLE_TIMESTAMP_PATTERN.match(timestamp.strip())
    if not match:
        raise ValueError(f"Invalid simple timestamp format: {timestamp}")

    minutes, seconds = map(int, match.groups())
    return (minutes * 60 + seconds) * 1000


def parse_simple(
    content: str, round_to_seconds: bool = False, default_duration_ms: int = 5000
) -> List[SubtitleEntry]:
    """Parse simple subtitle format and return a list of subtitle entries.

    Simple format uses single timestamps (M:SS) with text following each timestamp.
    End times are calculated as the start time of the next entry, or start + default_duration_ms
    for the last entry.

    Args:
        content: The full content of a simple subtitle file
        round_to_seconds: If True, round timestamps to whole seconds and convert to seconds
        default_duration_ms: Duration in milliseconds to use for last entry (default: 5000)

    Returns:
        List of SubtitleEntry dictionaries

    Raises:
        ValueError: If content is empty
    """
    if not content.strip():
        raise ValueError("Cannot parse empty content")

    entries: List[SubtitleEntry] = []
    lines = content.split("\n")
    entry_id = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this line is a timestamp
        if SIMPLE_TIMESTAMP_PATTERN.match(line):
            entry_id += 1
            start_ms = parse_simple_timestamp(line)

            # Collect text lines until we hit another timestamp or end
            text_lines = []
            i += 1
            while i < len(lines):
                text_line = lines[i]
                stripped = text_line.strip()
                # Stop if we hit another timestamp
                if SIMPLE_TIMESTAMP_PATTERN.match(stripped):
                    break
                # Skip empty lines within text
                if stripped:
                    text_lines.append(stripped)
                i += 1

            text = " ".join(text_lines).strip()

            # Store entry with temporary end time (will be updated)
            entries.append(
                {
                    "id": entry_id,
                    "start": start_ms,
                    "end": start_ms,  # Temporary, will be updated
                    "text": text,
                }
            )
        else:
            # Skip non-timestamp lines before first timestamp
            i += 1

    # Calculate end times based on next entry's start
    for i in range(len(entries)):
        if i < len(entries) - 1:
            # End time is the start of next entry
            entries[i]["end"] = entries[i + 1]["start"]
        else:
            # Last entry gets default duration
            entries[i]["end"] = entries[i]["start"] + default_duration_ms

    # Convert to seconds if requested
    if round_to_seconds:
        for entry in entries:
            entry["start"] = round(entry["start"] / 1000)
            entry["end"] = round(entry["end"] / 1000)

    return entries


def parse_subtitles(
    content: str,
    round_to_seconds: bool = False,
    format_hint: str = None,
    default_duration_ms: int = 5000,
) -> List[SubtitleEntry]:
    """Parse subtitle content with auto-detection of format.

    This is the recommended entry point for parsing subtitles. It automatically
    detects whether the content is in SBV or simple format and delegates to
    the appropriate parser.

    Args:
        content: The full content of a subtitle file
        round_to_seconds: If True, round timestamps to whole seconds and convert to seconds
        format_hint: Optional format hint ("sbv" or "simple") to skip detection
        default_duration_ms: Duration in milliseconds for last entry in simple format (default: 5000)

    Returns:
        List of SubtitleEntry dictionaries

    Raises:
        ValueError: If format cannot be detected or is invalid
    """
    # Use format hint if provided, otherwise auto-detect
    if format_hint:
        detected_format = format_hint
    else:
        detected_format = detect_format(content)

    if detected_format == "sbv":
        return parse_sbv(content, round_to_seconds=round_to_seconds)
    elif detected_format == "simple":
        return parse_simple(
            content,
            round_to_seconds=round_to_seconds,
            default_duration_ms=default_duration_ms,
        )
    else:
        raise ValueError(f"Unknown format: {detected_format}")

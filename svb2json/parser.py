"""SBV subtitle file parser."""

import re
from typing import List, TypedDict


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


def parse_sbv(content: str) -> List[SubtitleEntry]:
    """Parse SBV subtitle content and return a list of subtitle entries.

    Args:
        content: The full content of an SBV file

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
                text_lines.append(text_line.rstrip())
                i += 1

            text = "\n".join(text_lines)

            entries.append(
                {
                    "id": entry_id,
                    "start": start_ms,
                    "end": end_ms,
                    "text": text,
                }
            )
        else:
            # Skip non-timestamp lines that aren't part of an entry
            i += 1

    return entries

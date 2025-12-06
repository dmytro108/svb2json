"""Command-line interface for svb2txt."""

import argparse
import sys
from pathlib import Path

from .parser import parse_sbv, merge_subtitles, format_timestamp


def format_entry_as_text(entry: dict, timestamp_format: str, use_seconds: bool) -> str:
    """Format a subtitle entry as text: [start-end] text
    
    Args:
        entry: Subtitle entry dictionary
        timestamp_format: Format for timestamps
        use_seconds: Whether timestamps are in seconds
        
    Returns:
        Formatted string
    """
    start = entry["start"]
    end = entry["end"]
    
    # Format timestamps if needed
    if timestamp_format != "Mi" or use_seconds:
        start_formatted = format_timestamp(start if not use_seconds else start * 1000, timestamp_format)
        end_formatted = format_timestamp(end if not use_seconds else end * 1000, timestamp_format)
    else:
        start_formatted = start
        end_formatted = end
    
    return f"[{start_formatted}–{end_formatted}] {entry['text']}"


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="svb2txt",
        description="Convert YouTube SBV subtitles to text format.",
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Input SBV file path",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output text file path (default: stdout)",
    )
    parser.add_argument(
        "-s",
        "--seconds",
        action="store_true",
        help="Round timestamps to whole seconds and output in seconds instead of milliseconds",
    )
    parser.add_argument(
        "-m",
        "--merge",
        type=int,
        metavar="SECONDS",
        help="Merge subtitles into timeframes of specified duration in seconds",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        default="HH:MM:SS",
        choices=["HH:MM:SS.Mi", "HH:MM:SS", "HH:MM", "SS", "MM", "Mi"],
        help="Timestamp format (default: HH:MM:SS)",
    )

    args = parser.parse_args()

    # Validate merge argument
    if args.merge is not None and args.merge <= 0:
        print("Error: Merge duration must be positive", file=sys.stderr)
        return 1

    # Read input file
    input_path: Path = args.input
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        content = input_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Parse SBV content
    try:
        entries = parse_sbv(content, round_to_seconds=args.seconds)
    except ValueError as e:
        print(f"Error parsing SBV file: {e}", file=sys.stderr)
        return 1

    # Merge subtitles if requested
    if args.merge:
        entries = merge_subtitles(entries, args.merge, use_seconds=args.seconds)

    # Format as text
    text_lines = [
        format_entry_as_text(entry, args.format, args.seconds)
        for entry in entries
    ]
    text_output = "\n".join(text_lines)

    # Write output
    if args.output:
        try:
            args.output.write_text(text_output + "\n", encoding="utf-8")
        except OSError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        # Ensure UTF-8 encoding for stdout
        sys.stdout.reconfigure(encoding='utf-8')
        print(text_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command-line interface for svb2json."""

import argparse
import json
import sys
from pathlib import Path

from .parser import parse_sbv, merge_subtitles, format_timestamp


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="svb2json",
        description="Convert YouTube SBV subtitles to JSON format.",
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
        help="Output JSON file path (default: stdout)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2)",
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

    # Validate indent argument
    if args.indent is not None and args.indent < 0:
        print("Error: Indentation level cannot be negative", file=sys.stderr)
        return 1

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

    # Apply timestamp formatting if not using default milliseconds
    if args.format != "Mi" or args.seconds:
        for entry in entries:
            entry["start"] = format_timestamp(entry["start"] if not args.seconds else entry["start"] * 1000, args.format)
            entry["end"] = format_timestamp(entry["end"] if not args.seconds else entry["end"] * 1000, args.format)

    # Generate JSON output
    json_output = json.dumps(entries, indent=args.indent, ensure_ascii=False)

    # Write output
    if args.output:
        try:
            args.output.write_text(json_output + "\n", encoding="utf-8")
        except OSError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command-line interface for svb2json."""

import argparse
import json
import sys
from pathlib import Path

from .parser import parse_sbv


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

    args = parser.parse_args()

    # Read input file
    input_path: Path = args.input
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    # Parse SBV content
    try:
        entries = parse_sbv(content)
    except Exception as e:
        print(f"Error parsing SBV file: {e}", file=sys.stderr)
        return 1

    # Generate JSON output
    json_output = json.dumps(entries, indent=args.indent, ensure_ascii=False)

    # Write output
    if args.output:
        try:
            args.output.write_text(json_output + "\n", encoding="utf-8")
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

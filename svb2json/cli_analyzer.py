"""Command-line interface for SBV timing analysis."""

import argparse
import json
import sys
from pathlib import Path

from .parser import parse_subtitles
from .analyzer import analyze_subtitles, generate_statistics


def main() -> int:
    """Main entry point for the timing analyzer CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="analyze_sbv",
        description="Analyze timing anomalies in SBV subtitle files.",
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
        "--gap-threshold",
        type=int,
        default=1000,
        metavar="MS",
        help="Minimum gap duration in milliseconds to report (default: 1000)",
    )
    parser.add_argument(
        "--min-phrase",
        type=int,
        default=300,
        metavar="MS",
        help="Minimum acceptable phrase duration in milliseconds (default: 300)",
    )
    parser.add_argument(
        "--silence-threshold",
        type=int,
        default=3000,
        metavar="MS",
        help="Minimum duration in milliseconds to consider as silence (default: 3000)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2)",
    )
    parser.add_argument(
        "--include-stats",
        action="store_true",
        help="Include summary statistics in the output",
    )

    args = parser.parse_args()

    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file '{args.input}' does not exist", file=sys.stderr)
        return 1

    # Validate indent argument
    if args.indent is not None and args.indent < 0:
        print("Error: Indentation level cannot be negative", file=sys.stderr)
        return 1

    # Validate threshold arguments
    if args.gap_threshold <= 0:
        print("Error: Gap threshold must be positive", file=sys.stderr)
        return 1

    if args.min_phrase <= 0:
        print("Error: Minimum phrase duration must be positive", file=sys.stderr)
        return 1

    if args.silence_threshold <= 0:
        print("Error: Silence threshold must be positive", file=sys.stderr)
        return 1

    # Read and parse the SBV file
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    try:
        subtitles = parse_subtitles(content)
    except ValueError as e:
        print(f"Error parsing SBV file: {e}", file=sys.stderr)
        return 1

    # Analyze for timing anomalies
    anomalies = analyze_subtitles(
        subtitles,
        gap_threshold_ms=args.gap_threshold,
        min_phrase_ms=args.min_phrase,
        silence_threshold_ms=args.silence_threshold
    )

    # Build output structure
    output = {
        "file": str(args.input),
        "total_subtitles": len(subtitles),
        "anomalies": anomalies
    }

    if args.include_stats:
        output["statistics"] = generate_statistics(anomalies)

    # Generate JSON output
    json_output = json.dumps(output, indent=args.indent, ensure_ascii=False)

    # Write output
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"Analysis complete. Found {len(anomalies)} anomalies.", file=sys.stderr)
            print(f"Results written to: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return 1
    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

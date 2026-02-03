# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

svb2json is a Python CLI tool with two main functions:
1. Converting YouTube SBV subtitle files to JSON or text format
2. Chunking files (JSON and text) by LLM token limits while preserving structure

The project provides three CLI commands: `svb2json`, `svb2txt`, and `chunk2tokens`.

## Development Commands

### Installation
```bash
pip install .
```

For development with test dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run specific test class
pytest tests/test_parser.py::TestParseTimestamp

# Run specific test method
pytest tests/test_parser.py::TestParseTimestamp::test_simple_timestamp

# Run with verbose output
pytest -v
```

### Running the CLI Tools

Test the tools during development:
```bash
# Test svb2json
python -m svb2json.cli input.sbv -o output.json

# Test svb2txt
python -m svb2json.cli_txt input.sbv -o output.txt

# Test chunk2tokens
python -m svb2json.chunk2tokens file.json -t 800 -m GPT5
```

## Architecture

### Core Components

The codebase is organized around a shared parsing module and three independent CLI entry points:

**[svb2json/parser.py](svb2json/parser.py)** - Core parsing logic (shared by both svb2json and svb2txt):
- `parse_sbv()`: Main parser that converts SBV content to list of subtitle entries
- `parse_timestamp()`: Converts SBV timestamp format (`h:mm:ss.mmm,h:mm:ss.mmm`) to milliseconds
- `format_timestamp()`: Formats millisecond timestamps to various display formats (HH:MM:SS, HH:MM, etc.)
- `merge_subtitles()`: Merges short subtitle entries into longer timeframes (smart merging that skips subtitles >= 2/3 of target duration)

**[svb2json/cli.py](svb2json/cli.py)** - JSON output CLI:
- Imports parser functions
- Handles argument parsing for JSON-specific options (indent level, output file)
- Formats output as JSON array with id, start, end, text fields

**[svb2json/cli_txt.py](svb2json/cli_txt.py)** - Text output CLI:
- Imports parser functions
- Outputs format: `[start–end] text` (note: uses en dash `–`, not hyphen)
- Shares timestamp formatting with JSON CLI but different output format

**[svb2json/chunk2tokens.py](svb2json/chunk2tokens.py)** - File chunking by token count (independent from SBV conversion):
- Uses tiktoken library for accurate LLM token counting
- `chunk_json_content()`: Intelligently splits JSON arrays/objects while maintaining valid JSON in each chunk
- `chunk_text_content()`: Splits text by paragraphs/lines, avoiding mid-sentence breaks
- Supports multiple LLM models (GPT-3, GPT-3.5, GPT-4, GPT-4O, GPT5, CODEX) with different token encodings
- Creates files with numeric suffixes: `filename-001.ext`, `filename-002.ext`, etc.

### Data Flow

**SBV Conversion Flow:**
1. User runs `svb2json` or `svb2txt` CLI
2. CLI reads SBV file and calls `parse_sbv()` from parser module
3. `parse_sbv()` uses `parse_timestamp()` to convert timestamp strings to milliseconds
4. Optional: `merge_subtitles()` combines short entries if `-m` flag provided
5. Optional: `format_timestamp()` converts milliseconds to display format if `-f` flag provided
6. CLI formats output as JSON or text and writes to file/stdout

**File Chunking Flow:**
1. User runs `chunk2tokens` CLI
2. File is read and type is detected (JSON vs text)
3. For JSON: `chunk_json_content()` splits by array items or object keys
4. For text: `chunk_text_content()` splits by lines/paragraphs
5. Token counting with tiktoken ensures chunks stay under limit
6. Chunks saved as separate files with numeric suffixes

### Key Design Patterns

**Shared Core, Multiple Interfaces**: parser.py contains all SBV parsing logic, used by both JSON and text CLIs. This prevents duplication and ensures consistent parsing behavior.

**Type Safety**: Uses TypedDict for SubtitleEntry to provide clear data structure contracts between parser and CLI layers.

**Encoding Models**: chunk2tokens maps model names (GPT-4, GPT5, etc.) to tiktoken encoding names (cl100k_base, o200k_base, etc.) via MODEL_ENCODINGS dict.

**Structure Preservation**: JSON chunking maintains valid JSON in each output file. If a single JSON item exceeds the token limit, it's included anyway to prevent data loss.

**Smart Merging**: The merge_subtitles() function has sophisticated logic - it only merges subtitles shorter than 2/3 of the target duration, preventing awkwardly merged long subtitles.

## Testing

Tests are organized by module in the [tests/](tests/) directory:
- [test_parser.py](tests/test_parser.py) - Core parsing, timestamp handling, subtitle merging
- [test_cli.py](tests/test_cli.py) - svb2json CLI argument handling and output
- [test_cli_txt.py](tests/test_cli_txt.py) - svb2txt CLI argument handling and text formatting
- [test_chunk2tokens.py](tests/test_chunk2tokens.py) - Token counting and chunking logic

Tests use pytest with class-based organization (TestParseTimestamp, TestParseSbv, TestMergeSubtitles, etc.).

## Common Tasks

**Adding a new timestamp format**:
1. Add format to choices list in cli.py and cli_txt.py argument parsers
2. Implement formatting logic in parser.py's format_timestamp() function
3. Add test cases in test_parser.py

**Supporting a new LLM model**:
1. Add model name and encoding to MODEL_ENCODINGS dict in chunk2tokens.py
2. Add to choices list in chunk2tokens argument parser

**Modifying SBV parsing behavior**:
- All parsing logic is in parser.py's parse_sbv() function
- TIMESTAMP_PATTERN regex defines valid timestamp format
- Tests in test_parser.py::TestParseSbv cover edge cases

## Dependencies

- **tiktoken** (>=0.5.0): Required for accurate token counting across different LLM models
- **pytest** (>=7.0): Test framework (dev dependency)

Python 3.10+ required (uses modern type hints like `tuple[int, int]`).

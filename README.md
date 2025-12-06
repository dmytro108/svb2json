# svb2json

A Python CLI tool to convert YouTube SBV subtitles to JSON or text format, and chunk files based on LLM token limits.

## Installation

```bash
pip install .
```

## Usage

### chunk2tokens - Chunk Files by Token Limit

Split large files into smaller chunks based on LLM token counts while preserving file structure.

```bash
# Chunk a JSON file with 800 tokens per chunk for GPT5
chunk2tokens input.json -t 800 -m GPT5

# Chunk a text file with 1000 tokens for GPT-4
chunk2tokens data.txt -t 1000 -m GPT-4

# Save chunks to a custom directory
chunk2tokens file.json -t 500 -m GPT-3.5 -o chunks/
```

**Features:**
- **Structure-aware chunking**: JSON files are split intelligently while maintaining valid JSON structure in each chunk
- **Multiple LLM models**: Supports GPT-3.5, GPT-4, GPT-4O, GPT5, GPT-3, and CODEX
- **Automatic file naming**: Creates files like `filename-01.ext`, `filename-02.ext`, etc.
- **Smart text splitting**: Text files are split by paragraphs/lines, avoiding mid-sentence breaks
- **Token-accurate counting**: Uses tiktoken library for precise token counting per model

**Options:**
- `-t, --tokens`: Maximum tokens per chunk (default: 800)
- `-m, --model`: LLM model for token counting (default: GPT5)
- `-o, --output`: Output directory for chunks (default: same as input file)

### svb2json - Convert to JSON

```bash
# Convert SBV to JSON and print to stdout
svb2json input.sbv

# Write output to a file
svb2json input.sbv -o output.json

# Customize indentation
svb2json input.sbv --indent 4

# Round timestamps to seconds
svb2json input.sbv -s

# Merge subtitles into 20-second timeframes
svb2json input.sbv -m 20

# Custom timestamp format (HH:MM:SS, HH:MM, SS, MM, Mi)
svb2json input.sbv -f HH:MM:SS
```

### svb2txt - Convert to Text

```bash
# Convert SBV to text format and print to stdout
svb2txt input.sbv

# Write output to a file
svb2txt input.sbv -o output.txt

# Merge subtitles into 20-second timeframes
svb2txt input.sbv -m 20

# Custom timestamp format with milliseconds
svb2txt input.sbv -f HH:MM:SS.Mi

# Round timestamps to seconds
svb2txt input.sbv -s
```

## SBV Format

Each subtitle entry in the SBV format consists of:
- A timestamp line in `h:mm:ss.mmm,h:mm:ss.mmm` format (start,end)
- Text content (UTF-8 encoded)
- A blank line separator

Example:
```
0:00:01.000,0:00:03.000
Subtitle text 1

0:00:04.000,0:00:06.000
Subtitle text 2
```

## JSON Output

The `svb2json` tool outputs a JSON array with subtitle entries:

```json
[
  {
    "id": 1,
    "start": 1000,
    "end": 3000,
    "text": "Subtitle text 1"
  },
  {
    "id": 2,
    "start": 4000,
    "end": 6000,
    "text": "Subtitle text 2"
  }
]
```

- `id`: Sequential identifier starting from 1
- `start`: Start time in milliseconds (or seconds with `-s` flag)
- `end`: End time in milliseconds (or seconds with `-s` flag)
- `text`: Subtitle text content

## Text Output

The `svb2txt` tool outputs text in the format `[start–end] text`:

```
[00:00:01–00:00:03] Subtitle text 1
[00:00:04–00:00:06] Subtitle text 2
```

Each line contains:
- Timestamp range in brackets (format controlled by `-f` flag)
- En dash (–) separator between start and end times
- Subtitle text content

## License

MIT

# svb2json

A Python CLI tool to convert YouTube SBV subtitles to JSON format.

## Installation

```bash
pip install .
```

## Usage

```bash
# Convert SBV to JSON and print to stdout
svb2json input.sbv

# Write output to a file
svb2json input.sbv -o output.json

# Customize indentation
svb2json input.sbv --indent 4
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

The tool outputs a JSON array with subtitle entries:

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
- `start`: Start time in milliseconds
- `end`: End time in milliseconds
- `text`: Subtitle text content

## License

MIT

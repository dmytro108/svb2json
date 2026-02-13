# analyze_sbv - Usage Examples

The `analyze_sbv` tool detects timing anomalies in SBV subtitle files: gaps between phrases, too-short phrases, and silence periods.

## Basic Usage

### Analyze a file and save results
```bash
analyze_sbv input.sbv -o analysis.json
```

### Print analysis to console
```bash
analyze_sbv input.sbv
```

### Include summary statistics
```bash
analyze_sbv input.sbv -o report.json --include-stats
```

## Anomaly Types

### 1. Gaps
Pauses between consecutive subtitles where `(next_subtitle.start - current_subtitle.end) >= gap_threshold`.

**Severity Levels:**
- **Low**: 1-2 seconds (typical short pauses)
- **Medium**: 2-5 seconds (noticeable pauses)
- **High**: 5+ seconds (long pauses)

### 2. Short Phrases
Subtitles with duration below the minimum threshold, which may be too brief to read.

**Severity Levels:**
- **Low**: 200-300 ms (slightly short)
- **Medium**: 100-200 ms (very short)
- **High**: < 100 ms (extremely short, possibly errors)

### 3. Silence
Extended periods with no subtitles, typically indicating scene changes or intentional pauses.

**Severity**: Always **High**

## Customizing Thresholds

### Adjust gap detection
```bash
# Detect gaps of 500ms or more (stricter)
analyze_sbv input.sbv --gap-threshold 500

# Detect only significant gaps of 2+ seconds
analyze_sbv input.sbv --gap-threshold 2000
```

### Adjust minimum phrase duration
```bash
# Stricter: flag phrases shorter than 500ms
analyze_sbv input.sbv --min-phrase 500

# More lenient: only flag very short phrases
analyze_sbv input.sbv --min-phrase 100
```

### Adjust silence threshold
```bash
# Consider 5+ seconds as silence (longer scenes)
analyze_sbv input.sbv --silence-threshold 5000

# Consider 1+ seconds as silence (very sensitive)
analyze_sbv input.sbv --silence-threshold 1000
```

### Combine custom thresholds
```bash
analyze_sbv input.sbv \
  --gap-threshold 500 \
  --min-phrase 200 \
  --silence-threshold 4000 \
  -o custom_analysis.json
```

## Output Format

### Basic Output Structure
```json
{
  "file": "input.sbv",
  "total_subtitles": 150,
  "anomalies": [
    {
      "type": "gap",
      "start_ms": 5000,
      "end_ms": 6500,
      "duration_ms": 1500,
      "severity": "low",
      "context": {
        "previous_subtitle_id": 3,
        "next_subtitle_id": 4,
        "previous_text": "This is the text before the gap",
        "next_text": "This is the text after the gap"
      }
    },
    {
      "type": "short_phrase",
      "start_ms": 12000,
      "end_ms": 12150,
      "duration_ms": 150,
      "severity": "medium",
      "context": {
        "subtitle_id": 8,
        "text": "Too fast",
        "text_length": 8
      }
    },
    {
      "type": "silence",
      "start_ms": 30000,
      "end_ms": 35000,
      "duration_ms": 5000,
      "severity": "high",
      "context": {
        "previous_subtitle_id": 20,
        "next_subtitle_id": 21,
        "gap_seconds": 5.0
      }
    }
  ]
}
```

### With Statistics (`--include-stats`)
```json
{
  "file": "input.sbv",
  "total_subtitles": 150,
  "statistics": {
    "total_anomalies": 15,
    "by_type": {
      "gap": 8,
      "short_phrase": 5,
      "silence": 2
    },
    "by_severity": {
      "low": 6,
      "medium": 5,
      "high": 4
    }
  },
  "anomalies": [
    ...
  ]
}
```

## Real-World Examples

### Quality Control for Subtitle Files
Check if subtitles meet quality standards:
```bash
# Ensure all phrases are at least 400ms and no gaps exceed 2s
analyze_sbv lecture.sbv \
  --min-phrase 400 \
  --gap-threshold 2000 \
  --include-stats \
  -o quality_report.json
```

### Detect Scene Changes
Find potential scene breaks in a video:
```bash
# Look for 3+ second silences
analyze_sbv movie.sbv \
  --silence-threshold 3000 \
  -o scene_breaks.json
```

### Identify Problematic Subtitles
Find subtitles that need manual review:
```bash
# Very strict: find all potentially problematic timings
analyze_sbv input.sbv \
  --gap-threshold 300 \
  --min-phrase 150 \
  --silence-threshold 2000 \
  --include-stats \
  -o review_needed.json
```

### Quick Overview
Get a console summary:
```bash
analyze_sbv input.sbv --include-stats | grep -E '"total_|"by_'
```

## Field Reference

### Anomaly Object Fields

| Field         | Type    | Description                                       |
| ------------- | ------- | ------------------------------------------------- |
| `type`        | string  | Anomaly type: "gap", "short_phrase", or "silence" |
| `start_ms`    | integer | Start timestamp in milliseconds                   |
| `end_ms`      | integer | End timestamp in milliseconds                     |
| `duration_ms` | integer | Duration of the anomaly in milliseconds           |
| `severity`    | string  | Severity level: "low", "medium", or "high"        |
| `context`     | object  | Additional context specific to anomaly type       |

### Context Fields by Type

**Gap Context:**
- `previous_subtitle_id`: ID of subtitle before the gap
- `next_subtitle_id`: ID of subtitle after the gap
- `previous_text`: First 50 characters of previous subtitle
- `next_text`: First 50 characters of next subtitle

**Short Phrase Context:**
- `subtitle_id`: ID of the short subtitle
- `text`: Full text of the subtitle
- `text_length`: Character count of the text

**Silence Context:**
- `previous_subtitle_id`: ID of subtitle before silence
- `next_subtitle_id`: ID of subtitle after silence
- `gap_seconds`: Duration of silence in seconds (rounded to 2 decimals)

## Tips

1. **Start with defaults**: The default thresholds (1000ms gap, 300ms min phrase, 3000ms silence) work well for most content.

2. **Adjust based on content type**:
   - **Fast-paced content** (news, vlogs): Use lower thresholds
   - **Slow-paced content** (lectures, documentaries): Use higher thresholds

3. **Focus on high-severity anomalies first**: These typically indicate real issues that need attention.

4. **Use statistics for overview**: The `--include-stats` flag gives a quick summary before diving into details.

5. **Combine with other tools**: Use `svb2json` or `svb2txt` to view the actual subtitle content alongside the analysis.

## Integration with Pipeline

```bash
# Full workflow: convert, analyze, and review
svb2json input.sbv -o subtitles.json
analyze_sbv input.sbv -o analysis.json --include-stats
svb2txt input.sbv -o readable.txt

# Review the files to fix issues identified in analysis.json
```

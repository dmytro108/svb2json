# chunk2tokens - Usage Examples

## Basic Usage

### Chunk a JSON file
```bash
chunk2tokens data.json -t 800 -m GPT5
```
This will create files like:
- `data-001.json`
- `data-002.json`
- `data-003.json`
- etc.

Each file will contain valid JSON and approximately 800 GPT5 tokens.

### Chunk a text file
```bash
chunk2tokens document.txt -t 1000 -m GPT-4
```
Creates:
- `document-01.txt`
- `document-02.txt`
- etc.

## Advanced Usage

### Use a custom output directory
```bash
chunk2tokens large_file.json -t 500 -o ./chunks/
```
All chunk files will be saved in the `chunks/` directory.

### Different LLM models
```bash
# For GPT-3.5
chunk2tokens file.json -t 800 -m GPT-3.5

# For GPT-4
chunk2tokens file.json -t 800 -m GPT-4

# For older GPT-3
chunk2tokens file.json -t 800 -m GPT-3
```

## Real-World Examples

### Processing API responses
If you have a large JSON response from an API:
```bash
chunk2tokens api_response.json -t 1500 -m GPT-4O -o ./processed/
```

### Breaking down transcripts
For long text transcripts:
```bash
chunk2tokens transcript.txt -t 2000 -m GPT5 -o ./transcript_chunks/
```

### Preparing data for LLM processing
When you need to process a large dataset with an LLM that has token limits:
```bash
chunk2tokens dataset.json -t 3000 -m GPT-4
```

## How It Works

### JSON Files
The tool intelligently splits JSON arrays and objects:
- **Arrays**: Splits by individual items while keeping each chunk as a valid JSON array
- **Objects**: Splits by top-level keys while maintaining valid JSON object structure
- **Large single items**: Includes them even if they exceed the token limit (to prevent data loss)

### Text Files
The tool splits text content smartly:
- Splits by paragraphs and lines
- Tries to avoid breaking sentences
- Preserves formatting and structure

## Tips

1. **Choose appropriate token limits**: Consider your LLM's context window. For GPT-4, you might use 4000-6000 tokens per chunk, leaving room for prompts and responses.

2. **Verify chunks**: After chunking JSON files, you can verify they're valid:
   ```bash
   python -m json.tool filename-001.json
   ```

3. **Process chunks in order**: The numeric suffixes maintain the original order, so you can process them sequentially.

4. **Clean up**: Remember to clean up chunk files when done:
   ```bash
   # PowerShell
   Remove-Item *-???.json
   
   # Bash
   rm *-???.json
   ```

## Supported Models

- **GPT-3.5**: Uses `cl100k_base` encoding
- **GPT-4**: Uses `cl100k_base` encoding
- **GPT-4O**: Uses `o200k_base` encoding
- **GPT5**: Uses `o200k_base` encoding (latest)
- **GPT-3**: Uses `p50k_base` encoding
- **CODEX**: Uses `p50k_base` encoding

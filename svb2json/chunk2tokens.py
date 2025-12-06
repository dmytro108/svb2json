"""
Chunk files into portions based on LLM token limits while preserving structure.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import tiktoken


# Token counting for different models
MODEL_ENCODINGS = {
    "GPT-3.5": "cl100k_base",
    "GPT-4": "cl100k_base",
    "GPT-4O": "o200k_base",
    "GPT5": "o200k_base",  # Using latest encoding
    "GPT-3": "p50k_base",
    "CODEX": "p50k_base",
}


def count_tokens(text: str, model: str = "GPT5") -> int:
    """Count tokens in text for specified model."""
    encoding_name = MODEL_ENCODINGS.get(model.upper(), "cl100k_base")
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to simple estimation if tiktoken fails
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4


def chunk_json_content(data: any, max_tokens: int, model: str) -> List[any]:
    """
    Chunk JSON data intelligently while preserving structure.
    Returns list of valid JSON chunks.
    """
    chunks = []
    
    if isinstance(data, list):
        current_chunk = []
        current_tokens = count_tokens("[]", model)
        
        for item in data:
            item_str = json.dumps(item, indent=2)
            item_tokens = count_tokens(item_str, model)
            
            # If single item exceeds max_tokens, include it anyway
            if item_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_tokens = count_tokens("[]", model)
                chunks.append([item])
                continue
            
            # Check if adding item would exceed limit
            test_chunk = current_chunk + [item]
            test_str = json.dumps(test_chunk, indent=2)
            test_tokens = count_tokens(test_str, model)
            
            if test_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [item]
                current_tokens = item_tokens
            else:
                current_chunk.append(item)
                current_tokens = test_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
    
    elif isinstance(data, dict):
        # For dict, try to split by top-level keys
        current_chunk = {}
        current_tokens = count_tokens("{}", model)
        
        for key, value in data.items():
            item_str = json.dumps({key: value}, indent=2)
            item_tokens = count_tokens(item_str, model)
            
            if item_tokens > max_tokens:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = {}
                chunks.append({key: value})
                continue
            
            test_chunk = {**current_chunk, key: value}
            test_str = json.dumps(test_chunk, indent=2)
            test_tokens = count_tokens(test_str, model)
            
            if test_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = {key: value}
            else:
                current_chunk[key] = value
        
        if current_chunk:
            chunks.append(current_chunk)
    else:
        # For primitive types, just return as single chunk
        chunks.append(data)
    
    return chunks if chunks else [data]


def chunk_text_content(text: str, max_tokens: int, model: str) -> List[str]:
    """
    Chunk plain text content by paragraphs/lines while staying under token limit.
    """
    chunks = []
    lines = text.split('\n')
    
    current_chunk = []
    current_tokens = 0
    
    for line in lines:
        line_with_newline = line + '\n'
        line_tokens = count_tokens(line_with_newline, model)
        
        # If single line exceeds max, split it by sentences or words
        if line_tokens > max_tokens:
            if current_chunk:
                chunks.append(''.join(current_chunk).rstrip('\n'))
                current_chunk = []
                current_tokens = 0
            
            # Try to split by sentences
            sentences = line.split('. ')
            for i, sentence in enumerate(sentences):
                sent = sentence + ('. ' if i < len(sentences) - 1 else '')
                sent_tokens = count_tokens(sent, model)
                
                if current_tokens + sent_tokens > max_tokens and current_chunk:
                    chunks.append(''.join(current_chunk).rstrip('\n'))
                    current_chunk = [sent]
                    current_tokens = sent_tokens
                else:
                    current_chunk.append(sent)
                    current_tokens += sent_tokens
            
            if current_chunk:
                current_chunk.append('\n')
            continue
        
        if current_tokens + line_tokens > max_tokens and current_chunk:
            chunks.append(''.join(current_chunk).rstrip('\n'))
            current_chunk = [line_with_newline]
            current_tokens = line_tokens
        else:
            current_chunk.append(line_with_newline)
            current_tokens += line_tokens
    
    if current_chunk:
        chunks.append(''.join(current_chunk).rstrip('\n'))
    
    return chunks if chunks else [text]


def chunk_file(filepath: Path, max_tokens: int, model: str) -> List[Tuple[str, str]]:
    """
    Chunk file content based on file type.
    Returns list of (content, extension) tuples.
    """
    try:
        content = filepath.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = filepath.read_text(encoding='latin-1')
    
    extension = filepath.suffix.lower()
    
    # Check if content is JSON
    if extension == '.json' or (extension and is_json_content(content)):
        try:
            data = json.loads(content)
            chunks = chunk_json_content(data, max_tokens, model)
            return [(json.dumps(chunk, indent=2, ensure_ascii=False), extension) 
                    for chunk in chunks]
        except json.JSONDecodeError:
            # Fall back to text chunking
            pass
    
    # Default to text chunking
    chunks = chunk_text_content(content, max_tokens, model)
    return [(chunk, extension) for chunk in chunks]


def is_json_content(content: str) -> bool:
    """Check if content appears to be JSON."""
    content = content.strip()
    return (content.startswith('{') and content.endswith('}')) or \
           (content.startswith('[') and content.endswith(']'))


def save_chunks(chunks: List[Tuple[str, str]], original_path: Path, output_dir: Optional[Path] = None):
    """Save chunks to separate files."""
    if output_dir is None:
        output_dir = original_path.parent
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    stem = original_path.stem
    
    # Determine number of digits needed for padding
    num_digits = len(str(len(chunks)))
    
    saved_files = []
    for i, (chunk_content, ext) in enumerate(chunks, 1):
        chunk_filename = f"{stem}-{str(i).zfill(num_digits)}{ext}"
        chunk_path = output_dir / chunk_filename
        
        chunk_path.write_text(chunk_content, encoding='utf-8')
        saved_files.append(chunk_path)
        print(f"Created: {chunk_path}")
    
    return saved_files


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chunk files based on LLM token limits while preserving structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chunk2tokens input.json -t 800 -m GPT5
  chunk2tokens data.txt -t 1000 -m GPT-4
  chunk2tokens file.json -t 500 -m GPT-3.5 -o chunks/
        """
    )
    
    parser.add_argument(
        "filename",
        type=str,
        help="Path to the file to chunk"
    )
    
    parser.add_argument(
        "-t", "--tokens",
        type=int,
        default=800,
        help="Maximum tokens per chunk (default: 800)"
    )
    
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="GPT5",
        choices=list(MODEL_ENCODINGS.keys()),
        help="LLM model for token counting (default: GPT5)"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output directory for chunks (default: same as input file)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.filename)
    if not input_path.exists():
        print(f"Error: File '{args.filename}' not found", file=sys.stderr)
        return 1
    
    if not input_path.is_file():
        print(f"Error: '{args.filename}' is not a file", file=sys.stderr)
        return 1
    
    # Parse output directory
    output_dir = Path(args.output) if args.output else None
    
    # Process file
    print(f"Chunking '{input_path}' with max {args.tokens} tokens ({args.model})...")
    
    try:
        chunks = chunk_file(input_path, args.tokens, args.model)
        print(f"Generated {len(chunks)} chunk(s)")
        
        saved_files = save_chunks(chunks, input_path, output_dir)
        
        print(f"\nSuccessfully created {len(saved_files)} file(s)")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

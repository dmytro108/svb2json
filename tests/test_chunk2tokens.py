"""Tests for chunk2tokens module."""

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from svb2json.chunk2tokens import (
    count_tokens,
    chunk_json_content,
    chunk_text_content,
    chunk_file,
    is_json_content,
    save_chunks,
)


class TestTokenCounting:
    """Test token counting functionality."""
    
    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "Hello, world!"
        tokens = count_tokens(text, "GPT5")
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_count_tokens_different_models(self):
        """Test token counting with different models."""
        text = "The quick brown fox jumps over the lazy dog"
        
        for model in ["GPT-3.5", "GPT-4", "GPT5"]:
            tokens = count_tokens(text, model)
            assert tokens > 0
    
    def test_count_tokens_empty(self):
        """Test counting tokens in empty string."""
        tokens = count_tokens("", "GPT5")
        assert tokens == 0


class TestJSONChunking:
    """Test JSON content chunking."""
    
    def test_chunk_json_list(self):
        """Test chunking a JSON list."""
        data = [
            {"id": 1, "text": "First item"},
            {"id": 2, "text": "Second item"},
            {"id": 3, "text": "Third item"},
        ]
        
        chunks = chunk_json_content(data, max_tokens=50, model="GPT5")
        
        assert len(chunks) > 0
        # All chunks should be lists
        for chunk in chunks:
            assert isinstance(chunk, list)
        
        # Verify all items are preserved
        all_items = []
        for chunk in chunks:
            all_items.extend(chunk)
        assert len(all_items) == len(data)
    
    def test_chunk_json_dict(self):
        """Test chunking a JSON dictionary."""
        data = {
            "name": "Test",
            "description": "A test object",
            "items": [1, 2, 3],
            "metadata": {"created": "2025-01-01"}
        }
        
        chunks = chunk_json_content(data, max_tokens=50, model="GPT5")
        
        assert len(chunks) > 0
        # All chunks should be dicts
        for chunk in chunks:
            assert isinstance(chunk, dict)
    
    def test_chunk_json_small_content(self):
        """Test chunking content smaller than max_tokens."""
        data = [{"id": 1}]
        
        chunks = chunk_json_content(data, max_tokens=1000, model="GPT5")
        
        assert len(chunks) == 1
        assert chunks[0] == data
    
    def test_chunk_json_large_single_item(self):
        """Test chunking when single item exceeds max_tokens."""
        large_text = "x" * 10000
        data = [{"text": large_text}]
        
        chunks = chunk_json_content(data, max_tokens=100, model="GPT5")
        
        # Should still include the large item
        assert len(chunks) >= 1
        assert any(large_text in json.dumps(chunk) for chunk in chunks)


class TestTextChunking:
    """Test text content chunking."""
    
    def test_chunk_text_by_lines(self):
        """Test chunking text by lines."""
        text = "\n".join([f"Line {i}" for i in range(100)])
        
        chunks = chunk_text_content(text, max_tokens=50, model="GPT5")
        
        assert len(chunks) > 1
        # Each chunk should be a string
        for chunk in chunks:
            assert isinstance(chunk, str)
    
    def test_chunk_text_paragraphs(self):
        """Test chunking text with paragraphs."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        
        chunks = chunk_text_content(text, max_tokens=20, model="GPT5")
        
        assert len(chunks) > 0
        # Verify content is preserved
        combined = "\n".join(chunks)
        assert "Paragraph one" in combined
        assert "Paragraph three" in combined
    
    def test_chunk_text_small_content(self):
        """Test chunking small text."""
        text = "Short text"
        
        chunks = chunk_text_content(text, max_tokens=1000, model="GPT5")
        
        assert len(chunks) == 1
        assert chunks[0] == text


class TestFileChunking:
    """Test file chunking functionality."""
    
    def test_chunk_json_file(self):
        """Test chunking a JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            data = [{"id": i, "value": f"Item {i}"} for i in range(10)]
            json.dump(data, f, indent=2)
            temp_path = Path(f.name)
        
        try:
            chunks = chunk_file(temp_path, max_tokens=100, model="GPT5")
            
            assert len(chunks) > 0
            # Each chunk should be a tuple of (content, extension)
            for content, ext in chunks:
                assert isinstance(content, str)
                assert ext == '.json'
                # Verify it's valid JSON
                json.loads(content)
        finally:
            temp_path.unlink()
    
    def test_chunk_text_file(self):
        """Test chunking a text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("\n".join([f"Line {i}" for i in range(50)]))
            temp_path = Path(f.name)
        
        try:
            chunks = chunk_file(temp_path, max_tokens=100, model="GPT5")
            
            assert len(chunks) > 0
            for content, ext in chunks:
                assert isinstance(content, str)
                assert ext == '.txt'
        finally:
            temp_path.unlink()


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_is_json_content_valid(self):
        """Test JSON content detection with valid JSON."""
        assert is_json_content('{"key": "value"}')
        assert is_json_content('[1, 2, 3]')
        assert is_json_content('  {"key": "value"}  ')
    
    def test_is_json_content_invalid(self):
        """Test JSON content detection with invalid JSON."""
        assert not is_json_content('plain text')
        assert not is_json_content('key: value')
        assert not is_json_content('')


class TestSaveChunks:
    """Test saving chunks to files."""
    
    def test_save_chunks_basic(self):
        """Test basic chunk saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_path = tmpdir / "test.json"
            original_path.write_text('{"test": "data"}')
            
            chunks = [
                ('{"chunk": 1}', '.json'),
                ('{"chunk": 2}', '.json'),
            ]
            
            saved = save_chunks(chunks, original_path)
            
            assert len(saved) == 2
            assert (tmpdir / "test-1.json").exists()
            assert (tmpdir / "test-2.json").exists()
    
    def test_save_chunks_custom_output(self):
        """Test saving chunks to custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_path = tmpdir / "test.txt"
            output_dir = tmpdir / "chunks"
            
            chunks = [
                ('chunk 1', '.txt'),
                ('chunk 2', '.txt'),
            ]
            
            saved = save_chunks(chunks, original_path, output_dir)
            
            assert len(saved) == 2
            assert output_dir.exists()
            assert (output_dir / "test-1.txt").exists()
    
    def test_save_chunks_padding(self):
        """Test filename padding with many chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original_path = tmpdir / "test.txt"
            
            # Create 15 chunks to test padding
            chunks = [(f'chunk {i}', '.txt') for i in range(15)]
            
            saved = save_chunks(chunks, original_path)
            
            # Should use 2-digit padding
            assert (tmpdir / "test-01.txt").exists()
            assert (tmpdir / "test-15.txt").exists()

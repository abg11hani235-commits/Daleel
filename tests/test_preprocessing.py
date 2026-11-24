"""Tests for text cleaning and chunking."""
import pytest
from daleel.preprocessing.cleaner import TextCleaner
from daleel.preprocessing.chunker import BiomedicalChunker

def test_text_cleaner():
    cleaner = TextCleaner()
    assert cleaner.clean("  Sample Text  ") == "Sample Text"
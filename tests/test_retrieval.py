"""Tests for dense, BM25, and hybrid retrieval."""
import pytest
from daleel.retrieval.bm25_retriever import BM25Retriever

def test_bm25_retriever_initialization():
    retriever = BM25Retriever()
    assert retriever is not None
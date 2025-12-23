"""Tests for inverted index."""

import pytest

from logsearch.index.inverted_index import Document, InvertedIndex


def test_add_document():
    """Test adding documents to index."""
    index = InvertedIndex()
    doc = Document(
        id="1",
        timestamp=1000,
        content="This is a test log entry",
        source="app",
        level="INFO",
    )
    index.add_document(doc)
    assert index.total_docs == 1
    assert "1" in index.documents


def test_search_exact_match():
    """Test exact term matching."""
    index = InvertedIndex()
    doc1 = Document(id="1", timestamp=1000, content="error occurred", level="ERROR")
    doc2 = Document(id="2", timestamp=2000, content="success message", level="INFO")
    index.add_document(doc1)
    index.add_document(doc2)

    results = index.search("error")
    assert len(results) == 1
    assert results[0][0].id == "1"


def test_search_fuzzy_match():
    """Test fuzzy term matching."""
    index = InvertedIndex()
    doc = Document(id="1", timestamp=1000, content="error occurred", level="ERROR")
    index.add_document(doc)

    results = index.search("eror", fuzzy_threshold=70)  # typo
    assert len(results) > 0


def test_multiple_documents():
    """Test indexing multiple documents."""
    index = InvertedIndex()
    for i in range(10):
        doc = Document(
            id=str(i),
            timestamp=1000 + i,
            content=f"log entry {i} with some text",
        )
        index.add_document(doc)

    assert index.total_docs == 10
    results = index.search("entry")
    assert len(results) == 10


def test_index_stats():
    """Test index statistics."""
    index = InvertedIndex()
    doc = Document(id="1", timestamp=1000, content="test log entry")
    index.add_document(doc)

    stats = index.get_stats()
    assert stats["total_documents"] == 1
    assert stats["total_terms"] > 0


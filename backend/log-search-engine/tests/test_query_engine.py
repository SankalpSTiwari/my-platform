"""Tests for query engine."""

import pytest

from logsearch.index.inverted_index import Document
from logsearch.partition.time_partition import TimePartitionManager
from logsearch.query.query_engine import QueryEngine


def test_simple_query():
    """Test simple text query."""
    manager = TimePartitionManager()
    engine = QueryEngine(manager)

    doc = Document(id="1", timestamp=1000, content="error occurred", level="ERROR")
    manager.add_document(doc)

    result = engine.execute("error")
    assert result.total_count == 1
    assert len(result.documents) == 1


def test_field_filter_query():
    """Test query with field filters."""
    manager = TimePartitionManager()
    engine = QueryEngine(manager)

    doc1 = Document(id="1", timestamp=1000, content="error", level="ERROR")
    doc2 = Document(id="2", timestamp=2000, content="error", level="INFO")
    manager.add_document(doc1)
    manager.add_document(doc2)

    result = engine.execute("level:ERROR")
    assert result.total_count == 1
    assert result.documents[0].level == "ERROR"


def test_aggregation_query():
    """Test query with aggregations."""
    manager = TimePartitionManager()
    engine = QueryEngine(manager)

    for i, level in enumerate(["ERROR", "ERROR", "WARN", "INFO"]):
        doc = Document(
            id=str(i), timestamp=1000 + i, content="log", level=level
        )
        manager.add_document(doc)

    result = engine.execute("log | group by level")
    assert result.aggregations is not None
    assert "groups" in result.aggregations


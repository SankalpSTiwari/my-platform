"""Tests for time-based partitioning."""

import pytest

from logsearch.index.inverted_index import Document
from logsearch.partition.time_partition import TimePartition, TimePartitionManager


def test_partition_contains():
    """Test partition time range checking."""
    from logsearch.index.inverted_index import InvertedIndex
    partition = TimePartition(
        start_time=1000, end_time=2000, index=InvertedIndex()
    )
    assert partition.contains(1500)
    assert not partition.contains(500)
    assert not partition.contains(2500)


def test_partition_manager_add():
    """Test adding documents to partition manager."""
    manager = TimePartitionManager(partition_duration_ms=1000, max_partitions=10)

    doc1 = Document(id="1", timestamp=1000, content="log 1")
    doc2 = Document(id="2", timestamp=1500, content="log 2")
    doc3 = Document(id="3", timestamp=2500, content="log 3")

    manager.add_document(doc1)
    manager.add_document(doc2)
    manager.add_document(doc3)

    assert len(manager.partitions) == 2  # Two different partitions


def test_partition_manager_search():
    """Test searching across partitions."""
    manager = TimePartitionManager(partition_duration_ms=1000, max_partitions=10)

    doc1 = Document(id="1", timestamp=1000, content="error log")
    doc2 = Document(id="2", timestamp=2500, content="success log")
    manager.add_document(doc1)
    manager.add_document(doc2)

    results = manager.search("error")
    assert len(results) == 1
    assert results[0][0].id == "1"


def test_partition_manager_time_range():
    """Test searching with time range."""
    manager = TimePartitionManager(partition_duration_ms=1000, max_partitions=10)

    doc1 = Document(id="1", timestamp=1000, content="log 1")
    doc2 = Document(id="2", timestamp=5000, content="log 2")
    manager.add_document(doc1)
    manager.add_document(doc2)

    # Search only in first partition
    results = manager.search("log", start_time=0, end_time=2000)
    assert len(results) == 1
    assert results[0][0].id == "1"


def test_partition_cleanup():
    """Test automatic cleanup of old partitions."""
    manager = TimePartitionManager(partition_duration_ms=1000, max_partitions=3)

    # Add documents to 5 partitions
    for i in range(5):
        doc = Document(id=str(i), timestamp=i * 1000, content=f"log {i}")
        manager.add_document(doc)

    # Should only keep 3 partitions
    assert len(manager.partitions) <= 3


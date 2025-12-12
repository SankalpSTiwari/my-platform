"""Time-based partitioning for log storage and retrieval."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..index.inverted_index import Document, InvertedIndex


@dataclass
class TimePartition:
    """Represents a time-based partition of logs."""

    start_time: int  # Unix timestamp in milliseconds
    end_time: int
    index: InvertedIndex
    doc_count: int = 0

    def contains(self, timestamp: int) -> bool:
        """Check if timestamp falls within this partition."""
        return self.start_time <= timestamp < self.end_time

    def add_document(self, doc: Document) -> None:
        """Add a document to this partition."""
        if not self.contains(doc.timestamp):
            raise ValueError(
                f"Document timestamp {doc.timestamp} outside partition range "
                f"[{self.start_time}, {self.end_time})"
            )
        self.index.add_document(doc)
        self.doc_count += 1

    def search(self, query: str, **kwargs) -> List[tuple[Document, float]]:
        """Search within this partition."""
        return self.index.search(query, **kwargs)


class TimePartitionManager:
    """
    Manages time-based partitions for log storage.

    Partitions logs by time windows (e.g., hourly, daily) for efficient
    querying and automatic cleanup of old data.
    """

    def __init__(
        self,
        partition_duration_ms: int = 3600 * 1000,  # 1 hour default
        max_partitions: int = 24 * 7,  # 7 days of hourly partitions
    ):
        self.partition_duration_ms = partition_duration_ms
        self.max_partitions = max_partitions
        self.partitions: Dict[int, TimePartition] = {}  # key: partition_start_time

    def _get_partition_key(self, timestamp: int) -> int:
        """Get partition start time for a given timestamp."""
        return (timestamp // self.partition_duration_ms) * self.partition_duration_ms

    def add_document(self, doc: Document) -> None:
        """Add a document to the appropriate time partition."""
        partition_key = self._get_partition_key(doc.timestamp)
        end_time = partition_key + self.partition_duration_ms

        if partition_key not in self.partitions:
            self.partitions[partition_key] = TimePartition(
                start_time=partition_key,
                end_time=end_time,
                index=InvertedIndex(),
            )

        self.partitions[partition_key].add_document(doc)
        self._cleanup_old_partitions()

    def search(
        self,
        query: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        **kwargs,
    ) -> List[tuple[Document, float]]:
        """
        Search across partitions within a time range.

        Args:
            query: Search query
            start_time: Start timestamp (ms), None for all time
            end_time: End timestamp (ms), None for all time
            **kwargs: Additional search parameters

        Returns:
            Combined results from matching partitions, sorted by score
        """
        # Determine which partitions to search
        partitions_to_search = self._get_partitions_in_range(start_time, end_time)

        # Search each partition and combine results
        all_results: Dict[str, tuple[Document, float]] = {}
        for partition in partitions_to_search:
            results = partition.search(query, **kwargs)
            for doc, score in results:
                # Merge scores if document appears in multiple partitions
                if doc.id in all_results:
                    existing_doc, existing_score = all_results[doc.id]
                    all_results[doc.id] = (existing_doc, max(existing_score, score))
                else:
                    all_results[doc.id] = (doc, score)

        # Sort by score descending
        sorted_results = sorted(
            all_results.values(), key=lambda x: x[1], reverse=True
        )
        return sorted_results

    def _get_partitions_in_range(
        self, start_time: Optional[int], end_time: Optional[int]
    ) -> List[TimePartition]:
        """Get partitions that overlap with the time range."""
        partitions = []
        for partition_key, partition in self.partitions.items():
            # Check if partition overlaps with range
            if start_time is not None and partition.end_time <= start_time:
                continue
            if end_time is not None and partition.start_time >= end_time:
                continue
            partitions.append(partition)
        return partitions

    def _cleanup_old_partitions(self) -> None:
        """Remove old partitions to stay within max_partitions limit."""
        if len(self.partitions) <= self.max_partitions:
            return

        # Sort by start time and remove oldest
        sorted_keys = sorted(self.partitions.keys())
        keys_to_remove = sorted_keys[: len(self.partitions) - self.max_partitions]

        for key in keys_to_remove:
            del self.partitions[key]

    def get_partition_stats(self) -> Dict[str, int]:
        """Get statistics about partitions."""
        return {
            "total_partitions": len(self.partitions),
            "total_documents": sum(p.doc_count for p in self.partitions.values()),
            "oldest_partition": min(self.partitions.keys()) if self.partitions else 0,
            "newest_partition": max(self.partitions.keys()) if self.partitions else 0,
        }

    def clear(self) -> None:
        """Clear all partitions."""
        self.partitions.clear()


"""Query language and engine for log search with aggregations."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..index.inverted_index import Document
from ..partition.time_partition import TimePartitionManager


@dataclass
class QueryResult:
    """Result of a query execution."""

    documents: List[Document]
    total_count: int
    aggregations: Dict[str, Any] = None
    execution_time_ms: float = 0.0


class QueryParser:
    """Parses query strings into structured query objects."""

    # Query syntax examples:
    # "error" - simple text search
    # "level:ERROR AND message:timeout" - field filters with AND
    # "level:ERROR OR level:WARN" - OR conditions
    # "level:ERROR AND NOT source:test" - NOT conditions
    # "level:ERROR | group by level" - with aggregation
    # "level:ERROR | group by level, source | count" - multiple aggregations

    def __init__(self):
        self.field_pattern = re.compile(r"(\w+):([^\s]+)")
        self.aggregation_pattern = re.compile(
            r"\|\s*group\s+by\s+([\w,\s]+)(?:\s*\|\s*(\w+))?"
        )

    def parse(self, query_string: str) -> Dict[str, Any]:
        """Parse query string into structured format."""
        query_string = query_string.strip()

        # Extract aggregations
        aggregation_match = self.aggregation_pattern.search(query_string)
        group_by_fields = []
        aggregation_func = None

        if aggregation_match:
            group_by_str = aggregation_match.group(1)
            group_by_fields = [f.strip() for f in group_by_str.split(",")]
            aggregation_func = aggregation_match.group(2) or "count"
            # Remove aggregation from query string
            query_string = self.aggregation_pattern.sub("", query_string).strip()

        # Parse field filters and text search
        field_filters: Dict[str, List[str]] = defaultdict(list)
        text_terms = []

        # Split by AND/OR/NOT operators
        parts = re.split(r"\s+(AND|OR|NOT)\s+", query_string, flags=re.IGNORECASE)
        current_op = "AND"

        for part in parts:
            part = part.strip()
            if part.upper() in ("AND", "OR", "NOT"):
                current_op = part.upper()
                continue

            # Check for field filter
            field_match = self.field_pattern.match(part)
            if field_match:
                field_name = field_match.group(1)
                field_value = field_match.group(2)
                field_filters[field_name].append((current_op, field_value))
            else:
                # Text search term
                if part:
                    text_terms.append((current_op, part))

        return {
            "text_terms": text_terms,
            "field_filters": dict(field_filters),
            "group_by": group_by_fields,
            "aggregation": aggregation_func,
        }


class QueryEngine:
    """
    Executes queries against the log search engine.

    Supports:
    - Full-text search with fuzzy matching
    - Field-based filtering (level, source, etc.)
    - Boolean operators (AND, OR, NOT)
    - Aggregations (group by, count, etc.)
    - Time range filtering
    """

    def __init__(self, partition_manager: TimePartitionManager):
        self.partition_manager = partition_manager
        self.parser = QueryParser()

    def execute(
        self,
        query_string: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
        fuzzy_threshold: int = 80,
    ) -> QueryResult:
        """
        Execute a query and return results with aggregations.

        Args:
            query_string: Query in the query language
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Maximum number of documents to return
            fuzzy_threshold: Fuzzy matching threshold (0-100)

        Returns:
            QueryResult with documents and aggregations
        """
        import time

        start_exec = time.time()

        # Parse query
        parsed = self.parser.parse(query_string)

        # Build search query from text terms
        text_query = self._build_text_query(parsed["text_terms"])

        # Search partitions
        search_results = self.partition_manager.search(
            text_query,
            start_time=start_time,
            end_time=end_time,
            fuzzy_threshold=fuzzy_threshold,
            max_results=limit * 2,  # Get more for filtering
        )

        # Apply field filters
        filtered_docs = self._apply_field_filters(
            search_results, parsed["field_filters"]
        )

        # Limit results
        limited_docs = filtered_docs[:limit]

        # Compute aggregations if requested
        aggregations = {}
        if parsed["group_by"]:
            aggregations = self._compute_aggregations(
                limited_docs, parsed["group_by"], parsed["aggregation"]
            )

        execution_time = (time.time() - start_exec) * 1000

        return QueryResult(
            documents=[doc for doc, _ in limited_docs],
            total_count=len(filtered_docs),
            aggregations=aggregations,
            execution_time_ms=execution_time,
        )

    def _build_text_query(self, text_terms: List[tuple[str, str]]) -> str:
        """Build a text search query from parsed terms."""
        if not text_terms:
            return ""

        # For now, combine all terms with AND (can be enhanced)
        terms = []
        for op, term in text_terms:
            if op == "NOT":
                # Note: NOT handling would need more sophisticated logic
                continue
            terms.append(term)

        return " ".join(terms)

    def _apply_field_filters(
        self,
        search_results: List[tuple[Document, float]],
        field_filters: Dict[str, List[tuple[str, str]]],
    ) -> List[tuple[Document, float]]:
        """Apply field-based filters to search results."""
        if not field_filters:
            return search_results

        filtered = []
        for doc, score in search_results:
            match = True

            for field_name, conditions in field_filters.items():
                field_value = self._get_field_value(doc, field_name)

                field_match = False
                for op, filter_value in conditions:
                    if op == "AND" or op == "OR":
                        if field_value and filter_value.lower() in str(field_value).lower():
                            field_match = True
                            break
                    elif op == "NOT":
                        if field_value and filter_value.lower() not in str(field_value).lower():
                            field_match = True
                            break

                if not field_match:
                    match = False
                    break

            if match:
                filtered.append((doc, score))

        return filtered

    def _get_field_value(self, doc: Document, field_name: str) -> Optional[str]:
        """Get field value from document."""
        field_name_lower = field_name.lower()
        if field_name_lower == "level":
            return doc.level
        elif field_name_lower == "source":
            return doc.source
        elif field_name_lower in doc.metadata:
            return doc.metadata[field_name_lower]
        return None

    def _compute_aggregations(
        self,
        results: List[tuple[Document, float]],
        group_by_fields: List[str],
        aggregation_func: Optional[str],
    ) -> Dict[str, Any]:
        """Compute aggregations on query results."""
        if not results:
            return {}

        # Group documents
        groups: Dict[tuple, List[Document]] = defaultdict(list)
        for doc, _ in results:
            key_parts = []
            for field in group_by_fields:
                value = self._get_field_value(doc, field)
                key_parts.append(str(value) if value else "null")
            groups[tuple(key_parts)].append(doc)

        # Apply aggregation function
        aggregation_func = aggregation_func or "count"
        aggregated = {}

        for group_key, docs in groups.items():
            group_name = ", ".join(
                f"{field}={value}"
                for field, value in zip(group_by_fields, group_key)
            )

            if aggregation_func == "count":
                aggregated[group_name] = len(docs)
            elif aggregation_func == "sum":
                # Would need numeric field - placeholder
                aggregated[group_name] = len(docs)
            else:
                aggregated[group_name] = len(docs)

        return {"groups": aggregated, "total_groups": len(aggregated)}


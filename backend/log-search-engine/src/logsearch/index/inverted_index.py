"""Inverted index implementation for full-text log search."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

from rapidfuzz import fuzz


@dataclass
class Document:
    """Represents a log entry/document."""

    id: str
    timestamp: int  # Unix timestamp in milliseconds
    content: str
    source: str = ""
    level: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Posting:
    """Posting list entry for a term."""

    doc_id: str
    positions: List[int]  # Character positions where term appears
    score: float = 1.0  # TF-IDF or relevance score


class InvertedIndex:
    """
    Inverted index for efficient full-text search.

    Maps terms to posting lists containing document IDs and positions.
    Supports fuzzy matching using RapidFuzz.
    """

    def __init__(self):
        self.index: Dict[str, List[Posting]] = defaultdict(list)
        self.documents: Dict[str, Document] = {}
        self.doc_freq: Dict[str, int] = defaultdict(int)  # Document frequency per term
        self.total_docs = 0

    def add_document(self, doc: Document) -> None:
        """Add a document to the index."""
        if doc.id in self.documents:
            self._remove_document(doc.id)

        self.documents[doc.id] = doc
        self.total_docs += 1

        # Tokenize and index
        terms = self._tokenize(doc.content)
        term_positions: Dict[str, List[int]] = defaultdict(list)

        for term in terms:
            term_lower = term.lower()
            # Track positions for phrase matching
            positions = self._find_term_positions(doc.content, term)
            term_positions[term_lower].extend(positions)

        # Add to inverted index
        for term, positions in term_positions.items():
            posting = Posting(doc_id=doc.id, positions=positions)
            self.index[term].append(posting)
            if doc.id not in [p.doc_id for p in self.index[term][:-1]]:
                self.doc_freq[term] += 1

    def _remove_document(self, doc_id: str) -> None:
        """Remove a document from the index."""
        if doc_id not in self.documents:
            return

        # Remove from index
        for term in list(self.index.keys()):
            self.index[term] = [p for p in self.index[term] if p.doc_id != doc_id]
            if not self.index[term]:
                del self.index[term]
                if term in self.doc_freq:
                    del self.doc_freq[term]

        del self.documents[doc_id]
        self.total_docs = max(0, self.total_docs - 1)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms."""
        # Remove special chars, split on whitespace, keep alphanumeric
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.lower().split()
        # Filter out very short tokens
        return [t for t in tokens if len(t) >= 2]

    def _find_term_positions(self, text: str, term: str) -> List[int]:
        """Find all character positions where term appears (case-insensitive)."""
        positions = []
        text_lower = text.lower()
        term_lower = term.lower()
        start = 0
        while True:
            pos = text_lower.find(term_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions

    def search(
        self,
        query: str,
        fuzzy_threshold: int = 80,
        max_results: int = 100,
    ) -> List[tuple[Document, float]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query string
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching
            max_results: Maximum number of results to return

        Returns:
            List of (document, relevance_score) tuples, sorted by score descending
        """
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        doc_scores: Dict[str, float] = defaultdict(float)

        for term in query_terms:
            term_lower = term.lower()

            # Exact match
            if term_lower in self.index:
                self._score_documents(term_lower, doc_scores, exact=True)
            else:
                # Fuzzy match
                best_matches = self._fuzzy_match_term(term_lower, fuzzy_threshold)
                for matched_term, similarity in best_matches:
                    self._score_documents(matched_term, doc_scores, similarity / 100.0)

        # Sort by score and return top results
        sorted_docs = sorted(
            doc_scores.items(), key=lambda x: x[1], reverse=True
        )[:max_results]

        results = []
        for doc_id, score in sorted_docs:
            if doc_id in self.documents:
                results.append((self.documents[doc_id], score))

        return results

    def _fuzzy_match_term(
        self, query_term: str, threshold: int
    ) -> List[tuple[str, float]]:
        """Find terms in index that fuzzy match the query term."""
        matches = []
        for indexed_term in self.index.keys():
            similarity = fuzz.ratio(query_term, indexed_term)
            if similarity >= threshold:
                matches.append((indexed_term, similarity))
        # Sort by similarity descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:10]  # Top 10 fuzzy matches

    def _score_documents(
        self, term: str, doc_scores: Dict[str, float], similarity: float = 1.0
    ) -> None:
        """Score documents for a term using TF-IDF."""
        if term not in self.index:
            return

        # IDF (Inverse Document Frequency)
        idf = (
            math.log(self.total_docs / max(1, self.doc_freq[term]))
            if self.total_docs > 0
            else 0
        )

        for posting in self.index[term]:
            # TF (Term Frequency) - simple count of occurrences
            tf = len(posting.positions)
            # TF-IDF score
            tfidf = tf * idf * similarity
            doc_scores[posting.doc_id] += tfidf

    def get_stats(self) -> Dict[str, int]:
        """Get index statistics."""
        return {
            "total_documents": self.total_docs,
            "total_terms": len(self.index),
            "total_postings": sum(len(postings) for postings in self.index.values()),
        }

    def clear(self) -> None:
        """Clear the entire index."""
        self.index.clear()
        self.documents.clear()
        self.doc_freq.clear()
        self.total_docs = 0


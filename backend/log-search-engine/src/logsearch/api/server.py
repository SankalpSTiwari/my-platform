"""REST API server for log search engine."""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

from ..index.inverted_index import Document
from ..partition.time_partition import TimePartitionManager
from ..query.query_engine import QueryEngine

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Global engine instance
partition_manager: Optional[TimePartitionManager] = None
query_engine: Optional[QueryEngine] = None


def initialize_engine(
    partition_duration_ms: int = 3600 * 1000, max_partitions: int = 24 * 7
) -> None:
    """Initialize the search engine."""
    global partition_manager, query_engine
    partition_manager = TimePartitionManager(
        partition_duration_ms=partition_duration_ms, max_partitions=max_partitions
    )
    query_engine = QueryEngine(partition_manager)
    logger.info("Log search engine initialized")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "log-search-engine"})


@app.route("/api/logs", methods=["POST"])
def ingest_log():
    """Ingest a log entry."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract log fields
        content = data.get("message") or data.get("content", "")
        timestamp = data.get("timestamp")
        if timestamp:
            # Convert to milliseconds if needed
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = int(dt.timestamp() * 1000)
            elif timestamp < 1e12:  # Likely seconds, convert to ms
                timestamp = int(timestamp * 1000)
        else:
            timestamp = int(time.time() * 1000)

        doc = Document(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            content=content,
            source=data.get("source", ""),
            level=data.get("level", ""),
            metadata=data.get("metadata", {}),
        )

        partition_manager.add_document(doc)
        return jsonify({"id": doc.id, "status": "ingested"}), 201

    except Exception as e:
        logger.exception("Error ingesting log")
        return jsonify({"error": str(e)}), 500


@app.route("/api/logs/batch", methods=["POST"])
def ingest_logs_batch():
    """Ingest multiple log entries."""
    try:
        data = request.json
        logs = data.get("logs", [])
        if not logs:
            return jsonify({"error": "No logs provided"}), 400

        ingested = []
        for log_data in logs:
            content = log_data.get("message") or log_data.get("content", "")
            timestamp = log_data.get("timestamp")
            if timestamp:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    timestamp = int(dt.timestamp() * 1000)
                elif timestamp < 1e12:
                    timestamp = int(timestamp * 1000)
            else:
                timestamp = int(time.time() * 1000)

            doc = Document(
                id=str(uuid.uuid4()),
                timestamp=timestamp,
                content=content,
                source=log_data.get("source", ""),
                level=log_data.get("level", ""),
                metadata=log_data.get("metadata", {}),
            )

            partition_manager.add_document(doc)
            ingested.append(doc.id)

        return jsonify({"ingested": len(ingested), "ids": ingested}), 201

    except Exception as e:
        logger.exception("Error ingesting logs batch")
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["GET", "POST"])
def search():
    """Search logs."""
    try:
        if request.method == "POST":
            data = request.json
            query = data.get("query", "")
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            limit = data.get("limit", 100)
            fuzzy_threshold = data.get("fuzzy_threshold", 80)
        else:
            query = request.args.get("q", "")
            start_time = request.args.get("start_time", type=int)
            end_time = request.args.get("end_time", type=int)
            limit = request.args.get("limit", 100, type=int)
            fuzzy_threshold = request.args.get("fuzzy_threshold", 80, type=int)

        if not query:
            return jsonify({"error": "Query parameter required"}), 400

        result = query_engine.execute(
            query,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            fuzzy_threshold=fuzzy_threshold,
        )

        # Format response
        response = {
            "query": query,
            "total_count": result.total_count,
            "returned_count": len(result.documents),
            "execution_time_ms": round(result.execution_time_ms, 2),
            "results": [
                {
                    "id": doc.id,
                    "timestamp": doc.timestamp,
                    "content": doc.content,
                    "source": doc.source,
                    "level": doc.level,
                    "metadata": doc.metadata,
                }
                for doc in result.documents
            ],
        }

        if result.aggregations:
            response["aggregations"] = result.aggregations

        return jsonify(response), 200

    except Exception as e:
        logger.exception("Error searching logs")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def stats():
    """Get engine statistics."""
    try:
        partition_stats = partition_manager.get_partition_stats()
        return jsonify(
            {
                "partitions": partition_stats,
                "status": "operational",
            }
        ), 200

    except Exception as e:
        logger.exception("Error getting stats")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    initialize_engine()
    app.run(host="0.0.0.0", port=5000, debug=True)


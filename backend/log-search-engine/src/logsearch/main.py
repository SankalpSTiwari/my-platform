"""Main entry point for log search engine server."""

import logging
import sys

from logsearch.api.server import app, initialize_engine
from logsearch.config import Config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the log search engine server."""
    config = Config.from_env()
    logger.info("Starting log search engine with config: %s", config)

    initialize_engine(
        partition_duration_ms=config.partition_duration_ms,
        max_partitions=config.max_partitions,
    )

    logger.info("Server starting on %s:%s", config.api_host, config.api_port)
    app.run(host=config.api_host, port=config.api_port, debug=False)


if __name__ == "__main__":
    main()


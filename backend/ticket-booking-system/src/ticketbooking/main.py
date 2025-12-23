"""Main entry point for ticket booking system server."""

import logging
import sys

from ticketbooking.api.server import app, init_db
from ticketbooking.config import Config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the ticket booking system server."""
    config = Config.from_env()
    logger.info("Starting ticket booking system with config: %s", config)

    # Initialize database
    init_db(config.database_url)
    logger.info("Database initialized")

    # Initialize Redis client (optional)
    from ticketbooking.utils.redis_client import create_redis_client
    redis_client = create_redis_client(config)
    if redis_client:
        app.config["redis_client"] = redis_client

    logger.info("Server starting on %s:%s", config.api_host, config.api_port)
    app.config["config"] = config  # Store config in app for use in routes
    app.run(host=config.api_host, port=config.api_port, debug=False)


if __name__ == "__main__":
    main()


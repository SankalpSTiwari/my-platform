"""Main entry point for URL Shortener API Gateway."""

import logging
from urlshortener.api.gateway import app, init_app
from urlshortener.shared.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the URL Shortener API Gateway."""
    config = Config.from_env()
    logger.info("Starting URL Shortener API Gateway")
    logger.info(f"Configuration: {config}")
    
    init_app()
    
    logger.info(f"Server starting on {config.service_host}:{config.service_port}")
    app.run(host=config.service_host, port=config.service_port, debug=False)


if __name__ == "__main__":
    main()


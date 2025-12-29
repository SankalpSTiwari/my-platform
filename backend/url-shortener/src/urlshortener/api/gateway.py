"""API Gateway that routes to Write and Read services."""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from datetime import datetime
from sqlalchemy.orm import Session

from urlshortener.shared.config import Config
from urlshortener.shared.models.database import init_db, get_session_factory
from urlshortener.shared.utils.redis_client import RedisClient
from urlshortener.write_service.service import WriteService
from urlshortener.read_service.service import ReadService
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global instances
config = Config.from_env()
redis_client = RedisClient(config.redis_host, config.redis_port, config.redis_db)
SessionLocal = None


def init_app():
    """Initialize the application."""
    global SessionLocal
    
    # Initialize database
    init_db(config.database_url)
    SessionLocal = get_session_factory(config.database_url)
    logger.info("API Gateway initialized")


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "redis_available": redis_client.is_available()
    }), 200


@app.route("/urls", methods=["POST"])
def create_short_url():
    """Create a short URL (Write Service)."""
    db = next(get_db())
    try:
        data = request.get_json()
        
        if not data or "original_url" not in data:
            return jsonify({"error": "original_url is required"}), 400
        
        original_url = data["original_url"]
        custom_alias = data.get("custom_alias")
        expiration_time = None
        
        if data.get("expiration_time"):
            try:
                expiration_time = datetime.fromisoformat(
                    data["expiration_time"].replace("Z", "+00:00")
                )
            except ValueError:
                return jsonify({"error": "Invalid expiration_time format"}), 400
        
        user_id = data.get("user_id")
        
        write_service = WriteService(db, redis_client, config)
        short_url = write_service.create_short_url(
            original_url=original_url,
            custom_alias=custom_alias,
            expiration_time=expiration_time,
            user_id=user_id,
        )
        
        return jsonify({"short_url": short_url}), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating short URL: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


@app.route("/<short_code>", methods=["GET"])
def redirect_short_url(short_code: str):
    """Redirect short URL to original URL (Read Service)."""
    db = next(get_db())
    try:
        read_service = ReadService(db, redis_client, config)
        original_url, is_expired = read_service.get_original_url(short_code)
        
        if original_url:
            # Redirect to original URL
            return redirect(original_url, code=302)
        elif is_expired:
            # URL exists but is expired
            return jsonify({"error": "URL has expired"}), 404
        else:
            # URL not found
            return jsonify({"error": "Short URL not found"}), 404
            
    except Exception as e:
        logger.error(f"Error redirecting short URL: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


if __name__ == "__main__":
    init_app()
    app.run(host=config.service_host, port=config.service_port, debug=False)




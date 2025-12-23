"""Flask API server for ticket booking system."""

from datetime import datetime
from typing import Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ticketbooking.config import Config
from ticketbooking.models.database import Base
from ticketbooking.services.event_service import EventService
from ticketbooking.services.booking_service import BookingService
from ticketbooking.services.ticket_service import TicketService
from ticketbooking.utils.redis_client import create_redis_client

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Database setup
engine = None
SessionLocal = None
config = Config.from_env()
redis_client = None


def init_db(database_url: str):
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    # Use SQLite-specific settings for local development
    if database_url.startswith("sqlite"):
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)


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
    return jsonify({"status": "healthy"}), 200


@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id: str):
    """Get event details by ID with venue, performer, and tickets."""
    db = next(get_db())
    try:
        event_service = EventService(db)
        event = event_service.get_event_by_id(event_id)

        if not event:
            return jsonify({"error": "Event not found"}), 404

        ticket_service = TicketService(db)
        tickets = ticket_service.get_tickets_for_event(event_id)

        # Convert to dict
        event_dict = {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "event_type": event.event_type,
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "image_url": event.image_url,
            "metadata": event.metadata,
        }

        if event.venue:
            event_dict["venue"] = {
                "id": event.venue.id,
                "name": event.venue.name,
                "address": event.venue.address,
                "city": event.venue.city,
                "state": event.venue.state,
                "zip_code": event.venue.zip_code,
                "country": event.venue.country,
                "capacity": event.venue.capacity,
                "seat_map": event.venue.seat_map,
            }

        if event.performer:
            event_dict["performer"] = {
                "id": event.performer.id,
                "name": event.performer.name,
                "description": event.performer.description,
                "image_url": event.performer.image_url,
            }

        event_dict["tickets"] = [
            {
                "id": t.id,
                "section": t.section,
                "row": t.row,
                "seat_number": t.seat_number,
                "price": t.price,
                "status": t.status.value,
            }
            for t in tickets
        ]

        return jsonify(event_dict), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route("/api/events/search", methods=["GET"])
def search_events():
    """Search for events with filters."""
    db = next(get_db())
    try:
        # Get query parameters
        keyword = request.args.get("keyword")
        start_date_str = request.args.get("start")
        end_date_str = request.args.get("end")
        event_type = request.args.get("event_type")
        city = request.args.get("city")
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 20))

        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        end_date = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        event_service = EventService(db)
        events = event_service.search_events(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            city=city,
            page=page,
            page_size=page_size,
        )

        events_dict = [
            {
                "id": e.id,
                "name": e.name,
                "description": e.description,
                "event_type": e.event_type,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "venue_id": e.venue_id,
                "image_url": e.image_url,
            }
            for e in events
        ]

        return jsonify(events_dict), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route("/api/bookings/<event_id>", methods=["POST"])
def create_booking(event_id: str):
    """Reserve tickets for an event."""
    db = next(get_db())
    try:
        data = request.get_json()
        user_id = data.get("userId") or data.get("user_id")
        ticket_ids = data.get("ticketIds") or data.get("ticket_ids", [])

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if not ticket_ids:
            return jsonify({"error": "ticket_ids is required"}), 400

        app_config = app.config.get("config", config)
        app_redis = app.config.get("redis_client", redis_client)
        booking_service = BookingService(db, app_config, app_redis)
        booking = booking_service.reserve_tickets(user_id, event_id, ticket_ids)

        if not booking:
            return jsonify({"error": "Tickets are not available"}), 409

        booking_dict = {
            "id": booking.id,
            "userId": booking.user_id,
            "eventId": booking.event_id,
            "ticketIds": booking.ticket_ids,
            "totalPrice": booking.total_price,
            "status": booking.status.value,
            "expiresAt": booking.expires_at.isoformat() if booking.expires_at else None,
        }

        return jsonify(booking_dict), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route("/api/bookings/<booking_id>/confirm", methods=["POST"])
def confirm_booking(booking_id: str):
    """Confirm a booking after payment."""
    db = next(get_db())
    try:
        data = request.get_json()
        payment_id = data.get("paymentId") or data.get("payment_id")

        if not payment_id:
            return jsonify({"error": "payment_id is required"}), 400

        app_config = app.config.get("config", config)
        app_redis = app.config.get("redis_client", redis_client)
        booking_service = BookingService(db, app_config, app_redis)
        booking = booking_service.confirm_booking(booking_id, payment_id)

        if not booking:
            return jsonify({"error": "Booking not found or cannot be confirmed"}), 404

        booking_dict = {
            "id": booking.id,
            "userId": booking.user_id,
            "eventId": booking.event_id,
            "ticketIds": booking.ticket_ids,
            "totalPrice": booking.total_price,
            "status": booking.status.value,
            "confirmedAt": booking.confirmed_at.isoformat() if booking.confirmed_at else None,
            "paymentId": booking.payment_id,
        }

        return jsonify(booking_dict), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


if __name__ == "__main__":
    init_db(config.database_url)
    redis_client = create_redis_client(config)
    app.config["config"] = config
    if redis_client:
        app.config["redis_client"] = redis_client
    app.run(host=config.api_host, port=config.api_port, debug=True)


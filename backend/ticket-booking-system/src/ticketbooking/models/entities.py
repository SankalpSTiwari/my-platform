"""Core data models for the ticket booking system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class BookingStatus(str, Enum):
    """Booking status enum."""

    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TicketStatus(str, Enum):
    """Ticket status enum."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    CANCELLED = "cancelled"


@dataclass
class Performer:
    """Represents a performer, artist, team, or group."""

    id: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Venue:
    """Represents a physical venue location."""

    id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    capacity: int
    seat_map: Optional[Dict] = None  # JSON structure for seat layout
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    """Represents an event."""

    id: str
    name: str
    description: str
    event_type: str  # concert, sports, theater, etc.
    start_time: datetime
    end_time: Optional[datetime] = None
    venue_id: str = ""
    performer_id: str = ""
    image_url: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    # Relationships (populated when fetching)
    venue: Optional[Venue] = None
    performer: Optional[Performer] = None


@dataclass
class Ticket:
    """Represents a single ticket for an event."""

    id: str
    event_id: str
    section: str
    row: str
    seat_number: str
    price: float
    status: TicketStatus = TicketStatus.AVAILABLE
    booking_id: Optional[str] = None
    reserved_until: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Booking:
    """Represents a booking/transaction."""

    id: str
    user_id: str
    event_id: str
    ticket_ids: List[str]
    total_price: float
    status: BookingStatus = BookingStatus.IN_PROGRESS
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    payment_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class User:
    """Represents a user."""

    id: str
    email: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = field(default_factory=dict)





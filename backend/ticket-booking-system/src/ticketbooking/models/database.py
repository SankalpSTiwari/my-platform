"""Database models and schemas using SQLAlchemy."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# Association table for many-to-many relationship between Events and Performers
event_performer = Table(
    "event_performer",
    Base.metadata,
    Column("event_id", String, ForeignKey("events.id"), primary_key=True),
    Column("performer_id", String, ForeignKey("performers.id"), primary_key=True),
)


class PerformerModel(Base):
    """Performer database model."""

    __tablename__ = "performers"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    extra_data = Column(JSON, default=dict)

    # Relationships
    events = relationship("EventModel", secondary=event_performer, back_populates="performers")


class VenueModel(Base):
    """Venue database model."""

    __tablename__ = "venues"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    seat_map = Column(JSON, nullable=True)
    extra_data = Column(JSON, default=dict)

    # Relationships
    events = relationship("EventModel", back_populates="venue")


class TicketStatusEnum(PyEnum):
    """Ticket status enum."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    CANCELLED = "cancelled"


class EventModel(Base):
    """Event database model."""

    __tablename__ = "events"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    event_type = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    venue_id = Column(String, ForeignKey("venues.id"), nullable=False)
    image_url = Column(String, nullable=True)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    venue = relationship("VenueModel", back_populates="events")
    performers = relationship("PerformerModel", secondary=event_performer, back_populates="events")
    tickets = relationship("TicketModel", back_populates="event", cascade="all, delete-orphan")
    bookings = relationship("BookingModel", back_populates="event")


class TicketModel(Base):
    """Ticket database model."""

    __tablename__ = "tickets"

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    section = Column(String, nullable=False)
    row = Column(String, nullable=False)
    seat_number = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(Enum(TicketStatusEnum), default=TicketStatusEnum.AVAILABLE, nullable=False)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=True)
    reserved_until = Column(DateTime, nullable=True)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("EventModel", back_populates="tickets")
    booking = relationship("BookingModel", back_populates="tickets")


class BookingStatusEnum(PyEnum):
    """Booking status enum."""

    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BookingModel(Base):
    """Booking database model."""

    __tablename__ = "bookings"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(Enum(BookingStatusEnum), default=BookingStatusEnum.IN_PROGRESS, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    payment_id = Column(String, nullable=True)
    extra_data = Column(JSON, default=dict)

    # Relationships
    event = relationship("EventModel", back_populates="bookings")
    tickets = relationship("TicketModel", back_populates="booking")


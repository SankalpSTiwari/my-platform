"""Booking service for handling ticket reservations and purchases."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from ticketbooking.config import Config
from ticketbooking.models.database import (
    BookingModel,
    TicketModel,
    EventModel,
    BookingStatusEnum,
    TicketStatusEnum,
)
from ticketbooking.models.entities import Booking, Ticket, BookingStatus, TicketStatus


class BookingService:
    """Service for booking operations."""

    def __init__(self, db: Session, config: Config, redis_client=None):
        """Initialize booking service."""
        self.db = db
        self.config = config
        self.redis_client = redis_client

    def reserve_tickets(
        self, user_id: str, event_id: str, ticket_ids: List[str]
    ) -> Optional[Booking]:
        """
        Reserve tickets for a user with distributed locking.

        Returns Booking if successful, None if tickets are unavailable.
        """
        # Check if event exists
        event = self.db.query(EventModel).filter(EventModel.id == event_id).first()
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Start transaction
        try:
            # Lock tickets using distributed lock (Redis)
            lock_key = f"ticket_lock:{event_id}:{':'.join(sorted(ticket_ids))}"
            if self.redis_client:
                # Try to acquire lock
                lock_acquired = self.redis_client.set(
                    lock_key,
                    user_id,
                    ex=self.config.booking_lock_ttl_seconds,
                    nx=True,  # Only set if not exists
                )
                if not lock_acquired:
                    return None  # Tickets are locked by another user

            # Check ticket availability and lock them in DB
            tickets = (
                self.db.query(TicketModel)
                .filter(
                    and_(
                        TicketModel.id.in_(ticket_ids),
                        TicketModel.event_id == event_id,
                        TicketModel.status == TicketStatusEnum.AVAILABLE,
                    )
                )
                .with_for_update()  # Row-level locking
                .all()
            )

            if len(tickets) != len(ticket_ids):
                # Not all tickets are available
                if self.redis_client:
                    self.redis_client.delete(lock_key)
                return None

            # Calculate total price
            total_price = sum(ticket.price for ticket in tickets)

            # Create booking
            booking_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(
                seconds=self.config.booking_lock_ttl_seconds
            )

            booking_model = BookingModel(
                id=booking_id,
                user_id=user_id,
                event_id=event_id,
                total_price=total_price,
                status=BookingStatusEnum.IN_PROGRESS,
                expires_at=expires_at,
            )
            self.db.add(booking_model)

            # Update ticket status to reserved
            reserved_until = expires_at
            for ticket in tickets:
                ticket.status = TicketStatusEnum.RESERVED
                ticket.booking_id = booking_id
                ticket.reserved_until = reserved_until

            self.db.commit()

            # Convert to entity
            booking = Booking(
                id=booking_model.id,
                user_id=booking_model.user_id,
                event_id=booking_model.event_id,
                ticket_ids=ticket_ids,
                total_price=booking_model.total_price,
                status=BookingStatus(booking_model.status.value),
                created_at=booking_model.created_at,
                expires_at=booking_model.expires_at,
                metadata=booking_model.extra_data or {},
            )

            return booking

        except Exception as e:
            self.db.rollback()
            if self.redis_client:
                self.redis_client.delete(lock_key)
            raise e

    def confirm_booking(self, booking_id: str, payment_id: str) -> Optional[Booking]:
        """
        Confirm a booking after successful payment.

        Updates ticket status to SOLD and booking status to CONFIRMED.
        """
        booking_model = (
            self.db.query(BookingModel)
            .filter(BookingModel.id == booking_id)
            .with_for_update()
            .first()
        )

        if not booking_model:
            return None

        if booking_model.status != BookingStatusEnum.IN_PROGRESS:
            return None  # Booking is not in progress

        if booking_model.expires_at and booking_model.expires_at < datetime.utcnow():
            # Booking expired
            booking_model.status = BookingStatusEnum.EXPIRED
            self._release_tickets(booking_id)
            self.db.commit()
            return None

        # Update booking
        booking_model.status = BookingStatusEnum.CONFIRMED
        booking_model.confirmed_at = datetime.utcnow()
        booking_model.payment_id = payment_id

        # Update tickets to SOLD
        tickets = (
            self.db.query(TicketModel)
            .filter(TicketModel.booking_id == booking_id)
            .all()
        )
        for ticket in tickets:
            ticket.status = TicketStatusEnum.SOLD

        self.db.commit()

        # Convert to entity
        booking = Booking(
            id=booking_model.id,
            user_id=booking_model.user_id,
            event_id=booking_model.event_id,
            ticket_ids=[t.id for t in tickets],
            total_price=booking_model.total_price,
            status=BookingStatus(booking_model.status.value),
            created_at=booking_model.created_at,
            expires_at=booking_model.expires_at,
            confirmed_at=booking_model.confirmed_at,
            payment_id=booking_model.payment_id,
            metadata=booking_model.metadata or {},
        )

        return booking

    def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking and release tickets."""
        booking_model = (
            self.db.query(BookingModel)
            .filter(BookingModel.id == booking_id)
            .with_for_update()
            .first()
        )

        if not booking_model:
            return False

        if booking_model.status == BookingStatusEnum.CONFIRMED:
            # Already confirmed, cannot cancel (would need refund logic)
            return False

        booking_model.status = BookingStatusEnum.CANCELLED
        self._release_tickets(booking_id)
        self.db.commit()
        return True

    def _release_tickets(self, booking_id: str) -> None:
        """Release tickets from a booking."""
        tickets = (
            self.db.query(TicketModel)
            .filter(TicketModel.booking_id == booking_id)
            .all()
        )
        for ticket in tickets:
            ticket.status = TicketStatusEnum.AVAILABLE
            ticket.booking_id = None
            ticket.reserved_until = None


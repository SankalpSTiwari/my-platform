"""Ticket service for handling ticket-related operations."""

from typing import List

from sqlalchemy.orm import Session

from ticketbooking.models.database import TicketModel, EventModel, TicketStatusEnum
from ticketbooking.models.entities import Ticket, TicketStatus


class TicketService:
    """Service for ticket operations."""

    def __init__(self, db: Session):
        """Initialize ticket service with database session."""
        self.db = db

    def get_tickets_for_event(self, event_id: str) -> List[Ticket]:
        """Get all tickets for an event."""
        # Verify event exists
        event = self.db.query(EventModel).filter(EventModel.id == event_id).first()
        if not event:
            return []

        ticket_models = (
            self.db.query(TicketModel)
            .filter(TicketModel.event_id == event_id)
            .all()
        )

        tickets = []
        for ticket_model in ticket_models:
            ticket = Ticket(
                id=ticket_model.id,
                event_id=ticket_model.event_id,
                section=ticket_model.section,
                row=ticket_model.row,
                seat_number=ticket_model.seat_number,
                price=ticket_model.price,
                status=TicketStatus(ticket_model.status.value),
                booking_id=ticket_model.booking_id,
                reserved_until=ticket_model.reserved_until,
                metadata=ticket_model.extra_data or {},
            )
            tickets.append(ticket)

        return tickets


"""Event service for handling event-related operations."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ticketbooking.models.database import EventModel, VenueModel, PerformerModel
from ticketbooking.models.entities import Event, Venue, Performer


class EventService:
    """Service for event operations."""

    def __init__(self, db: Session):
        """Initialize event service with database session."""
        self.db = db

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID with venue and performer details."""
        event_model = (
            self.db.query(EventModel)
            .filter(EventModel.id == event_id)
            .first()
        )

        if not event_model:
            return None

        # Load venue
        venue_model = (
            self.db.query(VenueModel)
            .filter(VenueModel.id == event_model.venue_id)
            .first()
        )

        # Load performers
        performer_models = event_model.performers

        venue = None
        if venue_model:
            venue = Venue(
                id=venue_model.id,
                name=venue_model.name,
                address=venue_model.address,
                city=venue_model.city,
                state=venue_model.state,
                zip_code=venue_model.zip_code,
                country=venue_model.country,
                capacity=venue_model.capacity,
                seat_map=venue_model.seat_map,
                metadata=venue_model.extra_data or {},
            )

        performers = []
        if performer_models:
            performers = [
                Performer(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    image_url=p.image_url,
                    metadata=p.extra_data or {},
                )
                for p in performer_models
            ]

        event = Event(
            id=event_model.id,
            name=event_model.name,
            description=event_model.description,
            event_type=event_model.event_type,
            start_time=event_model.start_time,
            end_time=event_model.end_time,
            venue_id=event_model.venue_id,
            performer_id=performers[0].id if performers else "",
            image_url=event_model.image_url,
            metadata=event_model.extra_data or {},
            venue=venue,
        )

        if performers:
            event.performer = performers[0]

        return event

    def search_events(
        self,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[Event]:
        """Search events with filters."""
        query = self.db.query(EventModel)

        # Join with venue for city filtering
        if city:
            query = query.join(VenueModel, EventModel.venue_id == VenueModel.id)

        # Apply filters
        if keyword:
            keyword_filter = or_(
                EventModel.name.ilike(f"%{keyword}%"),
                EventModel.description.ilike(f"%{keyword}%"),
            )
            query = query.filter(keyword_filter)

        if start_date:
            query = query.filter(EventModel.start_time >= start_date)

        if end_date:
            query = query.filter(EventModel.start_time <= end_date)

        if event_type:
            query = query.filter(EventModel.event_type == event_type)

        if city:
            query = query.filter(VenueModel.city.ilike(f"%{city}%"))

        # Pagination
        offset = (page - 1) * page_size
        event_models = query.offset(offset).limit(page_size).all()

        # Convert to entity objects
        events = []
        for event_model in event_models:
            event = Event(
                id=event_model.id,
                name=event_model.name,
                description=event_model.description,
                event_type=event_model.event_type,
                start_time=event_model.start_time,
                end_time=event_model.end_time,
                venue_id=event_model.venue_id,
                image_url=event_model.image_url,
                metadata=event_model.extra_data or {},
            )
            events.append(event)

        return events


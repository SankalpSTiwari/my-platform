"""Script to seed the database with dummy data."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ticketbooking.config import Config
from ticketbooking.models.database import (
    Base,
    PerformerModel,
    VenueModel,
    EventModel,
    TicketModel,
    TicketStatusEnum,
)


def seed_database():
    """Seed the database with sample data."""
    config = Config.from_env()
    
    # Create engine
    if config.database_url.startswith("sqlite"):
        engine = create_engine(config.database_url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(config.database_url)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create performers
        performer1 = PerformerModel(
            id=str(uuid.uuid4()),
            name="Taylor Swift",
            description="Grammy-winning pop artist",
            image_url="https://example.com/taylor-swift.jpg",
        )
        performer2 = PerformerModel(
            id=str(uuid.uuid4()),
            name="The Rolling Stones",
            description="Legendary rock band",
            image_url="https://example.com/rolling-stones.jpg",
        )
        performer3 = PerformerModel(
            id=str(uuid.uuid4()),
            name="Hamilton",
            description="Broadway musical",
            image_url="https://example.com/hamilton.jpg",
        )
        
        db.add(performer1)
        db.add(performer2)
        db.add(performer3)
        db.flush()
        
        # Create venues
        venue1 = VenueModel(
            id=str(uuid.uuid4()),
            name="Madison Square Garden",
            address="4 Pennsylvania Plaza",
            city="New York",
            state="NY",
            zip_code="10001",
            country="USA",
            capacity=20000,
            seat_map={
                "sections": ["A", "B", "C", "D"],
                "rows_per_section": 50,
                "seats_per_row": 20,
            },
        )
        venue2 = VenueModel(
            id=str(uuid.uuid4()),
            name="The O2 Arena",
            address="Peninsula Square",
            city="London",
            state="",
            zip_code="SE10 0DX",
            country="UK",
            capacity=20000,
            seat_map={
                "sections": ["1", "2", "3", "4"],
                "rows_per_section": 40,
                "seats_per_row": 25,
            },
        )
        venue3 = VenueModel(
            id=str(uuid.uuid4()),
            name="Richard Rodgers Theatre",
            address="226 W 46th St",
            city="New York",
            state="NY",
            zip_code="10036",
            country="USA",
            capacity=1300,
            seat_map={
                "sections": ["Orchestra", "Mezzanine", "Balcony"],
                "rows_per_section": 30,
                "seats_per_row": 15,
            },
        )
        
        db.add(venue1)
        db.add(venue2)
        db.add(venue3)
        db.flush()
        
        # Create events
        event1 = EventModel(
            id="event123",
            name="Taylor Swift: The Eras Tour",
            description="Join Taylor Swift for an unforgettable night featuring songs from all her eras.",
            event_type="concert",
            start_time=datetime.utcnow() + timedelta(days=30),
            end_time=datetime.utcnow() + timedelta(days=30, hours=3),
            venue_id=venue1.id,
            image_url="https://example.com/eras-tour.jpg",
        )
        event1.performers.append(performer1)
        
        event2 = EventModel(
            id=str(uuid.uuid4()),
            name="The Rolling Stones: Hackney Diamonds Tour",
            description="Experience rock legends live in concert.",
            event_type="concert",
            start_time=datetime.utcnow() + timedelta(days=45),
            end_time=datetime.utcnow() + timedelta(days=45, hours=2.5),
            venue_id=venue2.id,
            image_url="https://example.com/rolling-stones-tour.jpg",
        )
        event2.performers.append(performer2)
        
        event3 = EventModel(
            id=str(uuid.uuid4()),
            name="Hamilton: The Musical",
            description="Lin-Manuel Miranda's award-winning musical about Alexander Hamilton.",
            event_type="theater",
            start_time=datetime.utcnow() + timedelta(days=7),
            end_time=datetime.utcnow() + timedelta(days=7, hours=2.5),
            venue_id=venue3.id,
            image_url="https://example.com/hamilton-show.jpg",
        )
        event3.performers.append(performer3)
        
        db.add(event1)
        db.add(event2)
        db.add(event3)
        db.flush()
        
        # Create tickets for event1 (event123)
        tickets_event1 = []
        sections = ["A", "B", "C", "D"]
        prices = [150.0, 120.0, 90.0, 60.0]
        
        for section_idx, section in enumerate(sections):
            for row in range(1, 11):  # 10 rows per section
                for seat in range(1, 21):  # 20 seats per row
                    ticket = TicketModel(
                        id=str(uuid.uuid4()),
                        event_id=event1.id,
                        section=section,
                        row=str(row),
                        seat_number=str(seat),
                        price=prices[section_idx],
                        status=TicketStatusEnum.AVAILABLE,
                    )
                    tickets_event1.append(ticket)
        
        # Create tickets for event2
        tickets_event2 = []
        sections = ["1", "2", "3", "4"]
        prices = [200.0, 150.0, 100.0, 75.0]
        
        for section_idx, section in enumerate(sections):
            for row in range(1, 11):
                for seat in range(1, 21):
                    ticket = TicketModel(
                        id=str(uuid.uuid4()),
                        event_id=event2.id,
                        section=section,
                        row=str(row),
                        seat_number=str(seat),
                        price=prices[section_idx],
                        status=TicketStatusEnum.AVAILABLE,
                    )
                    tickets_event2.append(ticket)
        
        # Create tickets for event3 (Hamilton - smaller venue)
        tickets_event3 = []
        sections = ["Orchestra", "Mezzanine", "Balcony"]
        prices = [180.0, 120.0, 80.0]
        
        for section_idx, section in enumerate(sections):
            for row in range(1, 11):
                for seat in range(1, 16):
                    ticket = TicketModel(
                        id=str(uuid.uuid4()),
                        event_id=event3.id,
                        section=section,
                        row=str(row),
                        seat_number=str(seat),
                        price=prices[section_idx],
                        status=TicketStatusEnum.AVAILABLE,
                    )
                    tickets_event3.append(ticket)
        
        # Add all tickets
        for ticket in tickets_event1 + tickets_event2 + tickets_event3:
            db.add(ticket)
        
        db.commit()
        print("✅ Successfully seeded database with dummy data!")
        print(f"   - Created 3 events (including event123)")
        print(f"   - Created 3 venues")
        print(f"   - Created 3 performers")
        print(f"   - Created {len(tickets_event1 + tickets_event2 + tickets_event3)} tickets")
        print(f"\n   You can now test:")
        print(f"   curl http://localhost:5002/api/events/event123")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()


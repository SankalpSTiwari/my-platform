"""Database models using SQLAlchemy."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class URLMapping(Base):
    """URL mapping database model."""

    __tablename__ = "urls"

    short_code = Column(String(255), primary_key=True, nullable=False)
    original_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expiration_time = Column(DateTime, nullable=True)
    user_id = Column(String(36), nullable=True)  # UUID as string

    def __repr__(self):
        return f"<URLMapping(short_code='{self.short_code}', original_url='{self.original_url[:50]}...')>"

    def is_expired(self):
        """Check if the URL mapping has expired."""
        if self.expiration_time is None:
            return False
        return datetime.utcnow() > self.expiration_time


def init_db(database_url: str):
    """Initialize database connection and create tables."""
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    return engine


def get_session_factory(database_url: str):
    """Get database session factory."""
    engine = create_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


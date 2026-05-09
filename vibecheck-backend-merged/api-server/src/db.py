"""SQLAlchemy setup + seed data."""
import os
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vibecheck.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class VenueORM(Base):
    __tablename__ = "venues"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # cafe, bar, club
    capacity = Column(Integer, nullable=False)
    has_dancefloor = Column(Boolean, default=False)
    stream_path = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(VenueORM).first() is None:
        seed = [
            VenueORM(id="venue-001", name="Neon Lounge", type="club", capacity=120, has_dancefloor=True, stream_path="venue-001", lat=51.5074, lon=-0.1278),
            VenueORM(id="venue-002", name="The Quiet Cup", type="cafe", capacity=80, has_dancefloor=False, stream_path="venue-002", lat=51.5155, lon=-0.0922),
            VenueORM(id="venue-003", name="Warehouse 9", type="club", capacity=400, has_dancefloor=True, stream_path="venue-003", lat=51.5200, lon=-0.0800),
        ]
        db.add_all(seed)
        db.commit()
    db.close()

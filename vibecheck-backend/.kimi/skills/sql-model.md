# Skill: SQLAlchemy Model Template

## Copy-Paste Template

```python
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

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
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Adding a New Model

```python
class EventORM(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    venue_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
```

## Seed Data

```python
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(VenueORM).first() is None:
        seed = [
            VenueORM(id="venue-001", name="Neon Lounge", type="club", capacity=120, ...),
        ]
        db.add_all(seed)
        db.commit()
    db.close()
```

## CRUD Pattern

```python
def get_venue(db, venue_id: str):
    return db.query(VenueORM).filter(VenueORM.id == venue_id).first()

def create_venue(db, venue: VenueORM):
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue

def update_venue(db, venue_id: str, updates: dict):
    db.query(VenueORM).filter(VenueORM.id == venue_id).update(updates)
    db.commit()
```

# Rule 06: Database & Schema

## Technology

- **SQLAlchemy 2.0** with `declarative_base()`
- **SQLite** for local development (`sqlite:///./vibecheck.db`)
- **PostgreSQL** ready for production (change `DATABASE_URL` env var)

## Model Definition

```python
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class VenueORM(Base):
    __tablename__ = "venues"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    has_dancefloor = Column(Boolean, default=False)
    stream_path = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
```

## Adding a Column

For MVP, just add the column and restart. `Base.metadata.create_all()` will add the new column on SQLite (it does a CREATE TABLE IF NOT EXISTS). **Note:** SQLite cannot ALTER TABLE to add columns with defaults on existing rows easily. If you need that, use Alembic or manually migrate.

```python
class VenueORM(Base):
    # ... existing columns ...
    # new column
    has_outdoor_seating = Column(Boolean, default=False)
```

## Seeding

Seed data is injected in `init_db()`:

```python
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(VenueORM).first() is None:
        seed = [
            VenueORM(id="venue-001", name="Neon Lounge", ...),
        ]
        db.add_all(seed)
        db.commit()
    db.close()
```

## Sessions

Always close sessions:

```python
db = SessionLocal()
try:
    rows = db.query(VenueORM).all()
finally:
    db.close()
```

Or use context managers if you prefer.

## No Migrations (Yet)

For MVP, delete `vibecheck.db` and restart if schema changes break things. PostgreSQL production will use Alembic later.

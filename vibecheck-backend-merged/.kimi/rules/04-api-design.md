# Rule 04: API Design & FastAPI Patterns

## Endpoint Design

### URL Structure

```
GET    /                     → health check / welcome
GET    /docs                 → auto-generated Swagger UI
GET    /app/                 → static web player
GET    /venues               → list all venues
GET    /venues/{id}          → single venue metadata
GET    /venues/{id}/signals  → latest aggregated signals
POST   /venues/{id}/signals  → push signals (signal-service only)
GET    /venues/{id}/stream   → HLS URL for The Mirror
```

### Response Models

Always use Pydantic response models for typed endpoints:

```python
from fastapi import FastAPI
from models import Venue, VenueSignals

@app.get("/venues", response_model=List[Venue])
def list_venues():
    ...
```

### Error Handling

Use `HTTPException` with descriptive detail:

```python
from fastapi import HTTPException

@app.get("/venues/{venue_id}")
def get_venue(venue_id: str):
    row = db.query(VenueORM).filter(VenueORM.id == venue_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")
```

### CORS

Always allow all origins for development:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Static Files

The web player is served from `web-player/` via `StaticFiles`:

```python
from fastapi.staticfiles import StaticFiles
import pathlib

static_dir = pathlib.Path(__file__).parent.parent.parent / "web-player"
app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="static")
```

- Mount at `/app` (not `/`). The root `/` is reserved for the API welcome message.
- Use `html=True` so `/app/` serves `index.html`.

## Pydantic Schemas

All schemas live in `api-server/src/models.py`. Add new signal types here first:

```python
class BarQueueSignal(BaseModel):
    queue_count: int

class VenueSignals(BaseModel):
    venue_id: str
    timestamp: float
    occupancy: Optional[OccupancySignal] = None
    demographics: Optional[DemographicsSignal] = None
    dancefloor: Optional[DanceFloorSignal] = None
    bar_queue: Optional[BarQueueSignal] = None  # <-- add this
    vibe_zones: Optional[List[VibeZone]] = None
```

## Database

- Use SQLAlchemy 2.0 style (`select()`, not `query()` if rewriting).
- SQLite for local dev: `sqlite:///./vibecheck.db`
- `SessionLocal` is a thread-local sessionmaker. Always close sessions.
- Seed data is injected in `init_db()` if the table is empty.

## Signal Cache

The API keeps an in-memory dict `_signal_cache` updated by POST from signal-service. It is the single source of truth for live signals. Do not query Redis directly for signals in endpoints.

## Environment

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vibecheck.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

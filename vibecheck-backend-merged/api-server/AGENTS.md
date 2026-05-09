# API Server — Agent Instructions

## What This Service Does

Serves the REST API (FastAPI), stores venue metadata in SQLite, caches live signals in memory, and serves the static web player files.

## Entry Point

```bash
uvicorn api-server.src.main:app --host 0.0.0.0 --port 8000
```

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI app, middleware, routes, static file mount |
| `src/models.py` | Pydantic schemas for all API payloads |
| `src/db.py` | SQLAlchemy setup, SQLite, seed data |

## Constraints

1. **In-memory signal cache is the source of truth for live data.**
   `_signal_cache: Dict[str, VenueSignals]` is updated by POST from signal-service. Never query Redis directly in GET endpoints for signals.

2. **SQLite for local, PostgreSQL for prod.**
   `DATABASE_URL` env var controls this. SQLAlchemy handles both transparently.

3. **Static files mount at `/app`.**
   The root `/` is reserved for the API welcome message. Do not mount static files at `/`.

4. **CORS must be wide open for development.**
   `allow_origins=["*"]` is fine for local dev. Tighten for production.

5. **Seed data is idempotent.**
   `init_db()` checks if data exists before inserting. Safe to run on every startup.

## Adding an Endpoint

See `.kimi/skills/fastapi-endpoint.md` for a template.

Quick version:
1. Add Pydantic model in `src/models.py`
2. Add route in `src/main.py`
3. Test with `curl`

## Adding a Venue

See `.kimi/workflows/add-venue.md`.

Quick version:
1. Add `VenueORM` seed in `src/db.py`
2. Restart `./start-demo.sh`
3. Verify with `curl http://localhost:8000/venues`

## Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| `DATABASE_URL` | `sqlite:///./vibecheck.db` | SQLAlchemy connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (used for signal TTL cache) |

## Testing

```bash
source ../.venv/bin/activate
uvicorn api-server.src.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal:
```bash
curl http://localhost:8000/venues
curl http://localhost:8000/venues/venue-001/signals
curl http://localhost:8000/docs
```

## Common Issues

- **404 on `/venues`:** Static file mount hijacked the root. Make sure `app.mount("/app", ...)` not `app.mount("/", ...)`.
- **CORS errors from ngrok:** CORS middleware is already configured. If issues persist, check the ngrok URL is HTTPS.
- **SQLite locked:** Only one process can write at a time. Don't run multiple API servers on the same SQLite file.

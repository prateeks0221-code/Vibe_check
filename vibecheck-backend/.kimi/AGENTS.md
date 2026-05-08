# VibeCheck — Agent Root Instructions

You are working on **VibeCheck**, a real-time venue intelligence platform. The backend ingests live CCTV footage, runs computer vision inference, aggregates signals, and serves a mobile-first web player.

## Project Structure

```
vibecheck-backend/
├── .kimi/              # Rules, workflows, skills for AI agents
├── mediamtx/           # Stream router config + binary
├── cv-pipeline/        # Computer vision workers
├── signal-service/     # Rolling-window aggregator + vibe engine
├── api-server/         # FastAPI + static web player
└── web-player/         # hls.js frontend (served by FastAPI)
```

## Golden Rules (read before any edit)

1. **Privacy is non-negotiable.** The `Anonymizer` processor runs first on every frame. Faces are blurred before any frame leaves the pipeline. Never add facial recognition or biometric retention.

2. **Minimal changes.** Touch only what you need. Follow existing patterns. If a pattern exists in the codebase, use it.

3. **No database migrations for MVP.** SQLite is used locally. Schema changes are handled by SQLAlchemy `create_all()` on startup. For production, a migration tool will be introduced later.

4. **Every CV processor must inherit `BaseProcessor`.** See `cv-pipeline/src/processors/base.py`. The interface is: `process(frame, context) -> dict`.

5. **All inter-service communication goes through Redis pub/sub.** CV pipeline publishes `cv.raw.{venue_id}.{processor_name}`. Signal service subscribes. No direct Python imports between services.

6. **The web player is vanilla HTML/JS.** No frameworks. hls.js for video. Mobile-first CSS.

7. **Environment variables over hardcoded values.** Use `os.getenv()` with sensible defaults. Document new env vars in the README.

8. **FastAPI for API, Uvicorn for server.** Pydantic for schemas. SQLAlchemy for ORM. No Flask, no Django.

9. **Test before claiming done.** If you add a processor, run `./start-demo.sh` and verify signals appear at `/venues/{id}/signals`.

10. **Keep it stupidly simple.** No microservices yet. No Kubernetes yet. No GraphQL yet. The PRD defines exactly 5 features. Stay in scope.

## How to Use This Directory

- **`.kimi/rules/`** — Read the relevant rule before coding. Rules are numbered by priority.
- **`.kimi/workflows/`** — Step-by-step guides for common tasks (add venue, add processor, etc.).
- **`.kimi/skills/`** — Reusable code patterns and templates. Copy-paste the template, fill in your logic.

## Module-Specific Instructions

Each service directory contains its own `AGENTS.md` with deeper constraints. Read it when modifying that service.

- `cv-pipeline/AGENTS.md` — Processor lifecycle, frame handling, dummy mode
- `signal-service/AGENTS.md` — Aggregation windows, vibe engine rules, flush cadences
- `api-server/AGENTS.md` — Endpoint design, Pydantic schemas, CORS, static files

## Quick Links

- Start everything: `./start-demo.sh`
- Stop everything: `./stop-demo.sh`
- Local app: http://localhost:8000/app/
- API docs: http://localhost:8000/docs
- Mobile via ngrok: see README.md

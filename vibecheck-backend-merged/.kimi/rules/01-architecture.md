# Rule 01: Architecture & Service Boundaries

## Service Separation

The backend has 4 independent services. They must never import each other's source files directly.

| Service | Responsibility | Entry Point | Communication |
|---------|---------------|-------------|---------------|
| **cv-pipeline** | Frame grab, run processors, publish raw events | `cv-pipeline/src/main.py` | Redis pub/sub |
| **signal-service** | Subscribe to Redis, aggregate, run vibe engine | `signal-service/src/main.py` | Redis sub + REST POST to API |
| **api-server** | Serve REST API, store venue metadata, cache signals | `api-server/src/main.py` | Redis read + REST |
| **MediaMTX** | Route RTSP/HLS streams | `mediamtx/mediamtx` | None (standalone binary) |

### Forbidden Patterns

- ❌ Importing `cv_pipeline.src.processors` from `signal-service`
- ❌ Importing `api_server.src.models` from `cv-pipeline`
- ❌ Direct function calls between services
- ✅ Each service is a standalone Python process

## Data Flow

```
CCTV → MediaMTX (RTSP) → ffmpeg (-c:v copy) → HLS Server (:8081) → Web Player
                              ↓
                        cv-pipeline (reads RTSP from MediaMTX)
                              ↓
                        Redis pub/sub: cv.raw.{venue_id}.{processor}
                              ↓
                        signal-service (aggregates, vibe engine)
                              ↓
                        REST POST /venues/{id}/signals
                              ↓
                        api-server (in-memory cache)
                              ↓
                        Web Player polls every 5s
```

## Redis Channels

- Publish: `cv.raw.{venue_id}.{processor_name}` (JSON payload)
- Read: `signals:{venue_id}` (TTL 60s, optional)

## Port Assignment

| Port | Service | Changeable? |
|------|---------|-------------|
| 8000 | FastAPI + web player | Yes (update start-demo.sh) |
| 8081 | HLS HTTP server | Yes (update web-player JS) |
| 8888 | MediaMTX native HLS | No (hardcoded in mediamtx.yml) |
| 8554 | MediaMTX RTSP | No (hardcoded in mediamtx.yml) |
| 6379 | Redis | Yes (update REDIS_URL env) |

## When to Add a New Service

You probably don't need to. If you do:

1. Add a new top-level directory (e.g., `analytics-service/`)
2. Give it its own `requirements.txt`, `Dockerfile`, `AGENTS.md`
3. Connect via Redis or REST only
4. Register in `start-demo.sh` and `stop-demo.sh`
5. Document in README.md

## Environment Variables

All services read these:

| Var | Default | Description |
|-----|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `DATABASE_URL` | `sqlite:///./vibecheck.db` | SQLAlchemy connection |
| `MEDIAMTX_URL` | `http://localhost:8888` | MediaMTX API base |
| `API_SERVER_URL` | `http://localhost:8000` | FastAPI base |
| `DUMMY_MODE` | `true` | cv-pipeline uses synthetic frames |

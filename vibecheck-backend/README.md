# VibeCheck Backend — Dummy Buildable Architecture

A containerised, modular backend skeleton for the VibeCheck PRD (MVP v1.0). It is designed to be **buildable today** and **swappable tomorrow** — every CV module is a pluggable processor, every service is independently scalable, and the streaming layer is built on open-source standards.

## Architecture Overview

```
┌─────────────────┐     RTSP      ┌─────────────────┐
│  Venue CCTV     │──────────────▶│   MediaMTX      │
│  (existing)     │               │  (stream router)│
└─────────────────┘               └────────┬────────┘
                                           │ HLS/WebRTC
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
           ┌─────────────┐       ┌─────────────────┐    ┌──────────────┐
           │  Web Player │       │  CV Pipeline    │    │  Recording   │
           │  (The Mirror)│      │  (OpenCV + placeholders)  │    │  (buffer only) │
           └─────────────┘       └────────┬────────┘    └──────────────┘
                                          │
                                          ▼ Redis pub/sub
                               ┌─────────────────┐
                               │ Signal Service  │
                               │ (aggregator +   │
                               │  vibe engine)   │
                               └────────┬────────┘
                                        │ REST / WS
                                        ▼
                               ┌─────────────────┐
                               │  API Server     │
                               │  (FastAPI)      │
                               └────────┬────────┘
                                        │
                                        ▼
                               ┌─────────────────┐
                               │  Consumer       │
                               │  Frontend       │
                               └─────────────────┘
```

## Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Stream ingestion | [MediaMTX](https://github.com/bluenviron/mediamtx) | Open-source, RTSP/RTMP/HLS/WebRTC, zero-cost |
| Web player | hls.js + vanilla HTML | Free, works everywhere, <10s latency with HLS-Low-Latency |
| CV backend | Python 3.11 + OpenCV + NumPy | Placeholder processors ready for real model swap |
| Message bus | Redis pub/sub | Lightweight, no persistence overhead for live signals |
| API | FastAPI + Uvicorn | Auto-generated docs, async-native, easy to extend |
| Database | PostgreSQL 15 | Venue configs, baselines, descriptor banks |
| Orchestration | Docker Compose | Single-command up, per-service scaling path to K8s |

## Quick Start

```bash
cd vibecheck-backend
docker compose up --build
```

Services will be available at:
- **MediaMTX HLS** → http://localhost:8888
- **API docs** → http://localhost:8000/docs
- **Web player (The Mirror)** → http://localhost:8080
- **Redis** → localhost:6379
- **PostgreSQL** → localhost:5432

## Project Structure

```
vibecheck-backend/
├── docker-compose.yml          # One-command orchestration
├── mediamtx/
│   └── mediamtx.yml            # Stream paths, auth, HLS output
├── cv-pipeline/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # Frame grabber + dispatcher
│       ├── worker.py           # Per-venue processing loop
│       ├── processors/
│       │   ├── base.py         # Abstract processor interface
│       │   ├── anonymizer.py   # Face blur (privacy gate)
│       │   ├── occupancy.py    # Head counting placeholder
│       │   ├── demographics.py # Age/gender placeholder
│       │   └── dancefloor.py   # Optical flow placeholder
│       └── utils/
│           └── frame_grabber.py# HLS → OpenCV bridge
├── signal-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # Redis subscriber + aggregator
│       ├── aggregator.py       # Rolling windows, normalisation
│       ├── vibe_engine.py      # Rule-based descriptor matching
│       └── api_client.py       # Pushes to API server
├── api-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # FastAPI app
│       ├── models.py           # Pydantic schemas
│       └── db.py               # SQLAlchemy + seed data
├── web-player/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html              # hls.js player + signal overlay
└── shared/
    └── proto/                  # Future protobuf contracts
```

## CV Processor Module System

Each processor inherits from `BaseProcessor` and implements:
- `process(frame, context)` → returns typed dict
- `required_fps` → throttling hint
- `model_path` → where to load weights from

Swapping in a real YOLO / MediaPipe / ONNX model is a 5-line change inside the processor file.

## Signal Refresh Cadences (PRD-mapped)

| Signal | Source | Window | Refresh |
|--------|--------|--------|---------|
| Occupancy % | occupancy processor | 60s rolling | 60s |
| Age / Gender | demographics processor | 5m rolling | 5m |
| Dance Floor | dancefloor processor | 30s instantaneous | 30s |
| Vibe Zones | vibe engine rules | — | 5m or trigger |
| The Mirror | anonymized HLS | — | continuous |

## Dummy Data Mode

If no RTSP source is connected, the CV pipeline generates synthetic frames and random-but-plausible signal values so the frontend team can develop against a live API immediately.

## Extending

1. **Add a new CV module** → create `cv-pipeline/src/processors/your_module.py`, inherit `BaseProcessor`, register in `worker.py`.
2. **Add a new signal** → update the processor output schema, add aggregation logic in `signal-service/src/aggregator.py`, expose in `api-server/src/main.py`.
3. **Scale out** → run multiple `cv-pipeline` containers with `venue_id` shard keys, or move to Kubernetes with the same Compose definitions.

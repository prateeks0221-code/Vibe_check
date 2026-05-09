# VibeCheck — Venue Intelligence System

> Real-time crowd analytics pipeline: privacy-first CV inference → multi-window aggregation → rule-based vibe descriptor matching → live web dashboard.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Component Breakdown](#3-component-breakdown)
4. [Data Flow](#4-data-flow)
5. [Processing Pipeline (CV Signals)](#5-processing-pipeline-cv-signals)
6. [Signal Aggregation & Vibe Engine](#6-signal-aggregation--vibe-engine)
7. [Technology Stack](#7-technology-stack)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [Directory Structure](#9-directory-structure)
10. [Design Decisions](#10-design-decisions)

---

## 1. System Overview

VibeCheck ingests live video streams from venue cameras, runs a privacy-preserving computer vision pipeline to extract crowd signals, aggregates those signals over rolling time windows, and derives a human-readable "vibe" description for the venue in real time.

The system is designed around five core functions (F1–F5):

| Signal           | ID  | Mechanism                                  | Cadence   |
|------------------|-----|--------------------------------------------|-----------|
| Privacy Gate     | F1  | Cascading face detector + Gaussian blur    | 15 fps    |
| Occupancy        | F2  | HOG people detector / head count          | 1 fps     |
| Demographics     | F3  | Age bracket + gender estimation           | 0.5 fps   |
| Dancefloor Energy| F4  | Dense optical flow motion energy          | 2 fps     |
| Vibe Descriptor  | F5  | Rule matching on aggregated F2–F4 signals | 5 min     |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAM INGESTION LAYER                             │
│                                                                             │
│   RTSP/IP Cameras ──────────────────────────────────────────────────────┐  │
│   RTMP Sources  ────────────────────────────────────────────────────┐   │  │
│   Test Streams  ───────────────────────────────────────────────┐    │   │  │
│                                                                │    │   │  │
│                                            ┌───────────────────▼────▼───▼─┐│
│                                            │        MediaMTX               ││
│                                            │  RTSP :8554  RTMP :1935       ││
│                                            │  HLS  :8888  WebRTC :8889     ││
│                                            └───────┬───────────────────────┘│
└────────────────────────────────────────────────────┼────────────────────────┘
                                                     │
                          ┌──────────────────────────┼──────────────────────┐
                          │                          │                      │
                    RTSP frames               HLS segments                  │
                          │                  (disk: ./hls/)                 │
                          ▼                                                  │
┌─────────────────────────────────────────────────────────────────────┐    │
│                        CV PIPELINE LAYER                            │    │
│                                                                     │    │
│  ┌─────────────── VenueWorker (one per venue) ──────────────────┐  │    │
│  │                                                               │  │    │
│  │  FrameGrabber (OpenCV RTSP reader, 5 fps target)             │  │    │
│  │       │                                                       │  │    │
│  │       ▼                                                       │  │    │
│  │  ┌────────────────────────────────────────────────────────┐  │  │    │
│  │  │              Processor Chain (sequential)              │  │  │    │
│  │  │                                                        │  │  │    │
│  │  │  [F1] Anonymizer ──► blurred frame (never serialised)  │  │  │    │
│  │  │       │                                                 │  │  │    │
│  │  │       ▼ (anonymised frame only)                        │  │  │    │
│  │  │  [F2] Occupancy  ──► {"head_count": N}                 │  │  │    │
│  │  │  [F3] Demographics ► {"primary_age":..,"male_pct":..}  │  │  │    │
│  │  │  [F4] DanceFloor  ──► {"energy_score": 0-100}          │  │  │    │
│  │  │                                                        │  │  │    │
│  │  └────────────────────────┬───────────────────────────────┘  │  │    │
│  │                           │ JSON payloads only               │  │    │
│  └───────────────────────────┼───────────────────────────────┘  │    │
│                              │                                    │    │
└──────────────────────────────┼────────────────────────────────────┘    │
                               │ Redis Pub/Sub                           │
                               │ ch: cv.raw.{venue}.{processor}          │
                               ▼                                         │
┌──────────────────────────────────────────────────────────────────┐    │
│                     SIGNAL AGGREGATION LAYER                     │    │
│                                                                  │    │
│  ┌──────────── VenueAggregator (one per venue) ───────────────┐ │    │
│  │                                                             │ │    │
│  │  WindowBuffer (occupancy)     60 s → mean % + label tier   │ │    │
│  │  WindowBuffer (demographics) 300 s → modal age bracket     │ │    │
│  │  WindowBuffer (dancefloor)    30 s → normalised energy     │ │    │
│  │                                                             │ │    │
│  │  VibeEngine (F5) ──► rule match {occ%, age, energy, hour}  │ │    │
│  │                       → top 3 vibe descriptor labels        │ │    │
│  │                                                             │ │    │
│  └────────────────────────────┬────────────────────────────────┘ │    │
│                               │ HTTP POST /venues/{id}/signals   │    │
└───────────────────────────────┼──────────────────────────────────┘    │
                                │                                        │
                                ▼                                        │
┌──────────────────────────────────────────────────────────────────┐    │
│                     API + PERSISTENCE LAYER                      │    │
│                                                                  │    │
│  ┌──────────────────────────────┐   ┌──────────────────────────┐│    │
│  │  FastAPI Server (:8000)      │   │  PostgreSQL              ││    │
│  │                              │   │  venues table            ││    │
│  │  GET  /venues                │──►│  (metadata, capacity,    ││    │
│  │  GET  /venues/{id}           │   │   stream_path, geo)      ││    │
│  │  GET  /venues/{id}/signals   │   └──────────────────────────┘│    │
│  │  POST /venues/{id}/signals   │   ┌──────────────────────────┐│    │
│  │  GET  /app/* (static)        │   │  Redis KV Cache          ││    │
│  │                              │──►│  signals:{venue} TTL 60s ││    │
│  └──────────────────────────────┘   └──────────────────────────┘│    │
└──────────────────────────────────────────────────────┬───────────┘    │
                                                       │                │
                                                       │                │ HLS
                                                       ▼                │
┌──────────────────────────────────────────────────────────────────────┐│
│                        PRESENTATION LAYER                            ││
│                                                                      ││
│  ┌───────────────── Web Player (nginx :8080) ──────────────────────┐ ││
│  │                                                                  │ ││
│  │  index.html + HLS.js                                             │◄┘│
│  │                                                                  │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │  │
│  │  │ Live Video  │ │  Occupancy   │ │ Demographics │ │Danceflr │ │  │
│  │  │ (blurred    │ │  37%         │ │  25-34       │ │ Energy  │ │  │
│  │  │  faces)     │ │  Getting     │ │  55%M / 45%F │ │ 64/100  │ │  │
│  │  │             │ │  There       │ │              │ │ Active  │ │  │
│  │  └─────────────┘ └──────────────┘ └──────────────┘ └─────────┘ │  │
│  │                                                                  │  │
│  │  Vibe Zones:  [Cocktail crowd]  [Afterwork wind-down]            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 MediaMTX — Stream Orchestration

| Attribute  | Detail                                                          |
|------------|-----------------------------------------------------------------|
| Role       | Protocol bridge and HLS segment generator                      |
| Listens on | RTSP `:8554`, RTMP `:1935`, HLS `:8888`, WebRTC `:8889`        |
| Config     | `vibecheck-backend/mediamtx/mediamtx.yml`                      |
| Per-venue  | Dedicated FFmpeg `runOnReady` hook → transcodes stream to HLS   |
| Output     | `./hls/{venue}/index.m3u8` (~2 s segments, auto-rotating)     |
| Failure    | HLS manifest auto-rotates; upstream reconnects on drop          |

### 3.2 CV Pipeline — Computer Vision Workers

| Attribute       | Detail                                                        |
|-----------------|---------------------------------------------------------------|
| Role            | Per-venue inference workers; publish raw signal events        |
| Entry point     | `cv-pipeline/src/main.py` → spawns `VenueWorker` threads     |
| Frame source    | `utils/frame_grabber.py` — OpenCV RTSP reader (5 fps target) |
| Processor order | Anonymizer → Occupancy → Demographics → DanceFloor (serial)  |
| Output bus      | Redis Pub/Sub `cv.raw.{venue_id}.{processor}`                |
| Failure mode    | Per-processor exception is logged; worker loop continues      |
| Dummy mode      | Synthetic frames generated when stream is unavailable         |

Processor FPS throttle (each processor rate-limits independently):

```
Anonymizer    15 fps  — always first; downstream sees blurred frames only
Occupancy      1 fps  — HOG detector, compute-heavy
Demographics   0.5 fps — slowest; large aggregation window anyway
DanceFloor     2 fps  — optical flow requires minimal temporal resolution
```

### 3.3 Signal Service — Aggregation & Rules Engine

| Attribute     | Detail                                                          |
|---------------|-----------------------------------------------------------------|
| Role          | Converts per-frame events into smoothed venue-level signals     |
| Entry point   | `signal-service/src/main.py` — Redis pub/sub subscriber         |
| Per-venue     | `aggregator.py` — `VenueAggregator` with `WindowBuffer` per signal |
| Window sizes  | Occupancy 60 s · Demographics 300 s · DanceFloor 30 s          |
| Vibe Engine   | `vibe_engine.py` — descriptor rule bank, top-3 match scoring   |
| Output        | HTTP POST to API server `/venues/{id}/signals`                  |
| Cadence       | Every Redis message; VibeEngine re-evaluated every 5 min        |

### 3.4 API Server — REST Interface

| Attribute  | Detail                                                          |
|------------|-----------------------------------------------------------------|
| Role       | Single source of truth; cache façade for the web player         |
| Framework  | FastAPI 0.111.0 on port `8000`                                  |
| Database   | PostgreSQL — `venues` table via SQLAlchemy ORM                  |
| Cache      | Redis KV — `signals:{venue_id}`, TTL 60 s                      |
| Static     | Web player HTML mounted at `/app/`                              |

Endpoints:

```
GET  /venues                — list all venues (PostgreSQL)
GET  /venues/{id}           — single venue metadata
GET  /venues/{id}/signals   — latest signals (Redis → memory fallback)
POST /venues/{id}/signals   — ingest from signal-service
GET  /app/*                 — static web player
```

### 3.5 Web Player — Frontend Dashboard

| Attribute   | Detail                                                          |
|-------------|-----------------------------------------------------------------|
| Role        | Operator dashboard — live video + real-time signal cards        |
| Technology  | Single-page HTML + vanilla JS + HLS.js (no build step)          |
| Served by   | nginx container on port `8080`                                  |
| Video       | HLS.js → `http://localhost:8888/{venue}/index.m3u8`             |
| Polling     | `GET /venues/{id}/signals` every 5 seconds                      |
| Cards       | Occupancy, Demographics, DanceFloor energy, Vibe Zones          |

---

## 4. Data Flow

End-to-end sequence for a single frame from Venue-001:

```
1.  Camera         →  RTSP push     →  MediaMTX :8554
2.  MediaMTX       →  FFmpeg        →  HLS segments at ./hls/venue-001/
3.  FrameGrabber   →  OpenCV        →  raw BGR frame (5 fps)
4.  Anonymizer     →  face detect   →  Gaussian blur in place
                   →  Redis publish →  cv.raw.venue-001.anonymizer  {face_count:3}
5.  Occupancy      →  HOG detect    →  head_count=47
                   →  Redis publish →  cv.raw.venue-001.occupancy   {head_count:47}
6.  Demographics   →  model/dummy   →  age="25-34", male_pct=55
                   →  Redis publish →  cv.raw.venue-001.demographics {...}
7.  DanceFloor     →  optical flow  →  energy_score=35
                   →  Redis publish →  cv.raw.venue-001.dancefloor  {energy_score:35}
8.  Signal Service →  60 s buffer   →  mean occ = 45 heads → 37% of 120 cap → "Getting There"
                   →  300 s buffer  →  modal age "25-34", mean gender 55% M
                   →  30 s buffer   →  mean flow = 32 → normalised 64/100 → "Active"
9.  VibeEngine     →  rule match    →  ["Cocktail crowd", "Afterwork wind-down"]
10. Signal Service →  HTTP POST     →  API Server /venues/venue-001/signals
11. API Server     →  Redis KV set  →  signals:venue-001  (TTL 60 s)
12. Web Player     →  poll /signals →  render UI cards (5 s interval)
13. Browser        →  HLS.js        →  live video stream (blurred faces) from :8888
```

---

## 5. Processing Pipeline (CV Signals)

### Privacy-First Chain Design

All processors downstream of F1 receive only the **blurred frame**. Raw face pixels never reach Occupancy, Demographics, or DanceFloor — enforced by chain ordering, not by configuration.

```
raw_frame
    │
    ▼
[F1 Anonymizer]      detect faces, Gaussian blur, emit {face_count}
    │
    ▼  (anonymised_frame — blurred faces)
[F2 Occupancy]       HOG SVM people detector, emit {head_count, dummy_mode}
    │
    ▼
[F3 Demographics]    age bracket + gender estimation (dummy/OpenVINO slot),
                     emit {primary_age, male_pct, female_pct}
    │
    ▼
[F4 DanceFloor]      dense optical flow vs previous frame,
                     emit {energy_score 0-100, raw_score, state}
```

Each processor:
- Extends `BaseProcessor` (`processors/base.py`)
- Declares `target_fps` — worker loop rate-limits per processor independently
- Returns a typed dict payload published as JSON to Redis
- Runs in isolation: one failing processor does not halt others

### Inference Runtime Hook

`inference_runtime.py` is the reserved integration point for loading and managing ML model instances (weights: `yolov8n.pt`, `yolov8n-pose.pt`, `yolov8n-seg.pt`, `yolov8n-cls.pt`). Current processors use OpenCV HOG and placeholder estimation. Upgrading to full neural inference requires only populating this module and updating the relevant processor — the rest of the pipeline is unchanged.

---

## 6. Signal Aggregation & Vibe Engine

### Rolling Window Buffers

```
Processor      Window    Aggregation                       Output
───────────────────────────────────────────────────────────────────────
Occupancy       60 s     mean(head_count)                  % capacity + label tier
Demographics   300 s     modal(age_bracket), mean(gender)  primary bracket + gender split
DanceFloor      30 s     mean(raw_score) → normalise       0-100 score + state string
```

Occupancy label tiers (configurable thresholds):

```
< 10%    Empty
10–50%   Getting There
50–80%   Buzzing
> 80%    Packed
```

### Vibe Engine (F5)

The `VibeEngine` holds a named descriptor bank. Each descriptor specifies min/max bounds on occupancy percentage, age bracket, dancefloor energy, and hour-of-day. On each evaluation cycle it:

1. Receives current aggregated state for a venue
2. Counts how many rule clauses each descriptor satisfies (confidence = clause count)
3. Returns the **top-3 descriptors** by confidence score

Example descriptors: `Cocktail crowd`, `Afterwork wind-down`, `Late night rage`, `Pre-game warmup`, `Sunday chill`.

---

## 7. Technology Stack

| Layer              | Technology                               | Version  |
|--------------------|------------------------------------------|----------|
| Stream broker      | MediaMTX                                 | latest   |
| Stream codec       | FFmpeg                                   | system   |
| CV framework       | OpenCV                                   | 4.8+     |
| ML models          | Ultralytics YOLOv8n (det/pose/seg/cls)   | —        |
| ML runtime         | PyTorch                                  | 2.1.0    |
| CV pipeline lang   | Python                                   | 3.11     |
| Message bus        | Redis Pub/Sub + KV                       | 7        |
| API framework      | FastAPI + Uvicorn                        | 0.111.0  |
| ORM                | SQLAlchemy                               | 2.0.30   |
| Database           | PostgreSQL                               | 15       |
| Frontend player    | HLS.js (vanilla JS)                      | —        |
| Web server         | nginx                                    | alpine   |
| Container runtime  | Docker + Docker Compose                  | —        |

---

## 8. Infrastructure & Deployment

### Services (docker-compose)

```
Service          Port(s)          Depends On
──────────────────────────────────────────────────────
mediamtx         8554/8888/1935   —
redis            6379             —
postgres         5432             —
cv-pipeline      —                mediamtx, redis
signal-service   —                redis, api-server
api-server       8000             postgres, redis
web-player       8080             api-server, mediamtx
```

Start the full stack:

```bash
docker-compose up --build
```

Scale CV workers horizontally:

```bash
docker-compose up --scale cv-pipeline=3
```

Access the dashboard at `http://localhost:8080`.

### Adding a New Venue

1. Add a `paths` entry in `mediamtx/mediamtx.yml` with the FFmpeg transcoding hook
2. Insert a row into the `venues` table (or add to seed data in `api-server/src/db.py`)
3. Add the venue ID to the worker list in `cv-pipeline/src/main.py`

---

## 9. Directory Structure

```
vibecheck-backend/
├── api-server/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py               FastAPI app, all endpoints
│       ├── models.py             Pydantic schemas
│       └── db.py                 SQLAlchemy ORM, venue seed data
│
├── cv-pipeline/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── models/                   YOLOv8 .pt weight files
│   └── src/
│       ├── main.py               Worker orchestrator (venue list)
│       ├── worker.py             VenueWorker frame loop + Redis publish
│       ├── inference_runtime.py  Model lifecycle hook (reserved for YOLO)
│       ├── processors/
│       │   ├── base.py           BaseProcessor ABC
│       │   ├── anonymizer.py     F1: face detection + blur
│       │   ├── occupancy.py      F2: HOG head count
│       │   ├── demographics.py   F3: age bracket + gender estimation
│       │   └── dancefloor.py     F4: optical flow energy
│       └── utils/
│           └── frame_grabber.py  RTSP/HLS ingestion + dummy mode
│
├── signal-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py               Redis subscriber, cadence control
│       ├── aggregator.py         WindowBuffer, VenueAggregator
│       ├── vibe_engine.py        F5: descriptor rule bank + matching
│       └── api_client.py         HTTP POST to API server
│
├── web-player/
│   ├── Dockerfile                nginx container
│   ├── index.html                SPA: video player + signal cards
│   └── nginx.conf                Reverse proxy config
│
├── mediamtx/
│   ├── mediamtx.yml              Stream paths + FFmpeg hooks per venue
│   └── mediamtx                  Binary
│
├── hls/                          Runtime HLS segments (auto-generated)
│   └── {venue}/index.m3u8
│
├── merge-tools/                  Migration tooling for CV model upgrades
│   ├── merge_cv_integration.py
│   └── MERGE_GUIDE.md
│
├── scripts/                      Utility scripts
├── hls_server.py                 Standalone dev HLS server (:8081)
└── docker-compose.yml
```

---

## 10. Design Decisions

### Privacy at the pipeline boundary
Anonymization (F1) runs first, at the highest frame rate. Downstream processors receive only blurred frames. The pipeline emits JSON only — no frames are serialized, stored, or transmitted.

### Decoupled aggregation windows per signal
Occupancy changes at a faster timescale than demographics. Using independent rolling windows (30 s / 60 s / 300 s) rather than a single polling interval prevents fast signals from aliasing and slow signals from being under-sampled.

### Redis as the integration bus
Pub/Sub decouples CV workers from the aggregation layer. Adding a new consumer (alerting, historical recording) requires only a new subscriber — the CV pipeline is untouched. The same Redis instance doubles as a low-latency API cache.

### Rule-based vibe descriptors
The vibe engine uses explicit, auditable rules rather than a trained classifier. Operators can inspect and tune descriptor thresholds without retraining a model. Confidence is a transparent clause-count, not an opaque score.

### Stateless API server
The API server holds no mutable in-process state. Signals are read from Redis (with an in-memory fallback). This makes the service trivially horizontally scalable and safely restartable without data loss.

### YOLOv8 as the upgrade path
Model weight files are present in `cv-pipeline/models/`. The `inference_runtime.py` hook is the designated integration point for full YOLO inference. Upgrading a processor to use YOLO does not change the processor interface, the worker loop, or the aggregation layer.

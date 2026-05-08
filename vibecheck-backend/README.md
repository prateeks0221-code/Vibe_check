# VibeCheck Backend

Real-time venue intelligence backend for the VibeCheck MVP (PRD v1.0). Ingests live CCTV, runs computer vision inference, aggregates signals, and serves a mobile-first web player.

**Status:** Buildable and running natively on macOS. One-command start/stop. Swappable to real CCTV with a single line change.

---

## Architecture

```
Venue CCTV (or dummy) ──RTSP──▶  MediaMTX  ──RTSP──▶  ffmpeg (-c:v copy)
192.168.0.xxx                     :8554                    │
                                                           ▼
                                                    HLS Server :8081
                                                           │
                    ┌──────────────────────────────────────┼──────────────────────┐
                    │                                      │                      │
                    ▼                                      ▼                      ▼
           ┌─────────────┐                       ┌─────────────────┐      ┌──────────────┐
           │  Web Player │                       │  CV Pipeline    │      │ Signal Svc   │
           │  (hls.js)   │                       │  OpenCV + dummy │      │ Aggregator   │
           └─────────────┘                       │  processors     │      │ Vibe Engine  │
                                                └────────┬────────┘      └──────┬───────┘
                                                         │                      │
                                                         ▼ Redis pub/sub        ▼ REST
                                                  ┌─────────────────┐  ┌──────────────┐
                                                  │  Redis :6379    │  │  FastAPI     │
                                                  └─────────────────┘  │  :8000       │
                                                                         └──────────────┘
```

| Layer | Technology | Why |
|-------|-----------|-----|
| Stream router | [MediaMTX](https://github.com/bluenviron/mediamtx) | Open-source RTSP/HLS/WebRTC. Zero cost. |
| HLS output | ffmpeg + Python HTTP server | `-c:v copy` = passthrough, near-zero latency. |
| Web player | hls.js + vanilla HTML | Works on every phone. Mobile-first. |
| CV backend | Python 3.13 + OpenCV + NumPy | Pluggable processors. Swap in real models later. |
| Message bus | Redis pub/sub | No persistence overhead. Lightweight. |
| API | FastAPI + Uvicorn | Auto docs, async, extensible. |
| Database | SQLite (local) / PostgreSQL (prod) | SQLAlchemy handles both. |

---

## Prerequisites

You need a Mac with Homebrew installed.

```bash
# 1. Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install system dependencies
brew install ffmpeg redis

# 3. Ensure Python 3.13+ is available
python3 --version   # should print 3.13.x

# 4. Ensure ngrok is available (for mobile demo)
ngrok version       # should print v3.x
# If missing: brew install --cask ngrok
```

---

## Setup (First Time)

```bash
# 1. Clone the repo
git clone <repo-url>
cd vibecheck-backend

# 2. Download MediaMTX binary
# Already included in repo at mediamtx/mediamtx
# If you need to re-download:
curl -sL -o mediamtx.tar.gz "https://github.com/bluenviron/mediamtx/releases/download/v1.18.1/mediamtx_v1.18.1_darwin_arm64.tar.gz"
tar -xzf mediamtx.tar.gz -C mediamtx/

# 3. Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install Python dependencies
pip install fastapi uvicorn sqlalchemy redis opencv-python-headless numpy requests python-dotenv

# 5. Make scripts executable
chmod +x start-demo.sh stop-demo.sh
```

---

## Run

### Start everything

```bash
./start-demo.sh
```

Output shows:
```
Local web app:  http://localhost:8000/app/
API docs:       http://localhost:8000/docs
HLS endpoint:   http://localhost:8081
LAN web app:    http://192.168.0.103:8000/app/
```

Open http://localhost:8000/app/ in your browser.

### Stop everything

```bash
./stop-demo.sh
```

---

## View It on Your Phone

Run these in **two separate terminals**:

```bash
# Terminal 1 — API + web player
ngrok http 8000

# Terminal 2 — HLS video streams
ngrok http 8081
```

Then on your phone open:

```
https://<API-NGROK-HOST>.ngrok-free.app/app/?hls=<HLS-NGROK-HOST>.ngrok-free.app
```

Example:
```
https://31cf-45-119-31-90.ngrok-free.app/app/?hls=99cd-45-119-31-90.ngrok-free.app
```

---

## Connect a Real CCTV Camera

### 1. Edit the stream source

Open `mediamtx/mediamtx.yml` and change the venue you want:

```yaml
venue-001:
  source: rtsp://192.168.0.108:8080/h264_pcm.sdp
  # comment out or remove runOnInit when using a real camera
  # runOnInit: /opt/homebrew/bin/ffmpeg ...
  # runOnInitRestart: yes
```

### 2. Restart

```bash
./stop-demo.sh && ./start-demo.sh
```

That's it. The HLS generator automatically pulls from `rtsp://localhost:8554/venue-001`, which now proxies your real camera. No other files need changing.

### 3. Switch back to dummy feed

```yaml
venue-001:
  source: publisher
  runOnInit: /opt/homebrew/bin/ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=15 -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://localhost:8554/venue-001
  runOnInitRestart: yes
```

```bash
./stop-demo.sh && ./start-demo.sh
```

---

## Operations

### Service Map

| Service | Port | What it does |
|---------|------|-------------|
| FastAPI + Web Player | **8000** | API docs, venue data, signals, static HTML |
| HLS HTTP Server | **8081** | Serves `.m3u8` playlists and `.ts` segments |
| MediaMTX (RTSP) | **8554** | Ingests cameras / dummy feeds, re-streams RTSP |
| MediaMTX (native HLS) | **8888** | Optional — HLS straight from MediaMTX |
| Redis | **6379** | Message bus between CV and signal service |
| CV Pipeline | — | Reads video, runs face blur + occupancy + demographics + dancefloor |
| Signal Service | — | Aggregates rolling windows, runs vibe engine rules |

### Logs

```bash
# All logs
tail -f logs/*.log

# Specific services
tail -f logs/mediamtx.log
tail -f logs/cv-pipeline.log
tail -f logs/signal-service.log
tail -f logs/api-server.log
tail -f logs/hls-venue-001.log
tail -f logs/hls-venue-002.log
tail -f logs/hls-venue-003.log
```

### Health Checks

```bash
# API root
curl http://localhost:8000/

# Venue list
curl http://localhost:8000/venues

# Live signals
curl http://localhost:8000/venues/venue-001/signals

# HLS playlist
curl http://localhost:8081/venue-001/index.m3u8
```

### Restart Individual Services

**HLS generator only** (after changing a camera source):
```bash
pkill -f "ffmpeg.*rtsp://localhost:8554"
rm -f hls/venue-001/*.ts hls/venue-001/*.m3u8

/opt/homebrew/bin/ffmpeg \
  -rtsp_transport tcp -fflags +discardcorrupt \
  -i rtsp://localhost:8554/venue-001 \
  -c:v copy -an \
  -f hls -hls_time 2 -hls_list_size 15 \
  -hls_flags delete_segments+append_list \
  hls/venue-001/index.m3u8
```

**CV Pipeline only:**
```bash
pkill -f "python cv-pipeline/src/main.py"
source .venv/bin/activate
export PYTHONPATH="api-server/src:cv-pipeline/src:signal-service/src"
python cv-pipeline/src/main.py &
```

**API Server only:**
```bash
pkill -f "uvicorn api-server.src.main:app"
source .venv/bin/activate
uvicorn api-server.src.main:app --host 0.0.0.0 --port 8000 &
```

---

## Add a New Venue

### 1. `mediamtx/mediamtx.yml`

Add under `paths:`:

```yaml
venue-004:
  source: rtsp://192.168.0.200/stream
```

### 2. `api-server/src/db.py`

Add to the seed list in `init_db()`:

```python
VenueORM(id="venue-004", name="The Blue Door", type="bar", capacity=150, has_dancefloor=True, stream_path="venue-004", lat=51.5100, lon=-0.1000),
```

### 3. `cv-pipeline/src/main.py`

Add to `VENUES`:

```python
{"id": "venue-004", "capacity": 150, "has_dancefloor": True},
```

### 4. `signal-service/src/main.py`

Add to `VENUES`:

```python
"venue-004": {"capacity": 150, "has_dancefloor": True},
```

### 5. Restart

```bash
./stop-demo.sh && ./start-demo.sh
```

---

## Troubleshooting

### Video stuck on "loading"

```bash
# Check if HLS segments exist
ls hls/venue-001/

# Check ffmpeg is running
ps aux | grep "ffmpeg.*venue-001"

# Check the playlist
curl http://localhost:8081/venue-001/index.m3u8
```

### API returns 404 for /venues

Restart:
```bash
./stop-demo.sh && ./start-demo.sh
```

### ngrok URL changed

Free URLs rotate on restart. Grab the new ones:
```bash
curl -s http://localhost:4040/api/tunnels | grep public_url
curl -s http://localhost:4041/api/tunnels | grep public_url
```

### Port already in use

```bash
lsof -ti:8000 | xargs kill -9
lsof -ti:8081 | xargs kill -9
lsof -ti:8554 | xargs kill -9
```

### MediaMTX decode errors on real camera

Your camera may send incompatible audio or packet format. The HLS generator already uses `-c:v copy -an` (pass video through, drop audio). If issues persist, try adding `-rtsp_transport tcp` to the MediaMTX source config.

---

## Project Structure

```
vibecheck-backend/
├── README.md                   # This file
├── OPERATIONS.md               # Detailed ops reference
├── start-demo.sh               # One-command launcher
├── stop-demo.sh                # Kill all services
├── requirements-all.txt        # Python dependencies
├── hls_server.py               # Custom HLS HTTP server (CORS + no-cache)
│
├── mediamtx/
│   ├── mediamtx                # MediaMTX binary (Darwin arm64)
│   └── mediamtx.yml            # Stream paths and camera sources
│
├── cv-pipeline/
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # Venue discovery + worker orchestration
│       ├── worker.py           # Per-venue frame loop
│       ├── processors/
│       │   ├── base.py         # Abstract processor interface
│       │   ├── anonymizer.py   # Face blur (privacy gate)
│       │   ├── occupancy.py    # Head counting (HOG placeholder)
│       │   ├── demographics.py # Age/gender dummy
│       │   └── dancefloor.py   # Optical flow energy detector
│       └── utils/
│           └── frame_grabber.py# HLS/RTSP → OpenCV bridge
│
├── signal-service/
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # Redis subscriber
│       ├── aggregator.py       # Rolling windows (60s / 5m / 30s)
│       ├── vibe_engine.py      # Rule-based descriptor matching (F5)
│       └── api_client.py       # Pushes to REST API
│
├── api-server/
│   ├── requirements.txt
│   └── src/
│       ├── main.py             # FastAPI app + static files
│       ├── models.py           # Pydantic schemas
│       └── db.py               # SQLAlchemy + seed data (SQLite)
│
├── web-player/
│   └── index.html              # hls.js player + signal overlay
│
├── hls/                        # Generated HLS segments
│   ├── venue-001/
│   ├── venue-002/
│   └── venue-003/
│
└── logs/                       # Runtime logs
```

---

## PRD Feature Mapping

| PRD Feature | Backend Component | Refresh |
|-------------|-------------------|---------|
| **F1 — The Mirror** | MediaMTX HLS + ffmpeg `-c:v copy` + hls.js | Continuous |
| **F2 — Occupancy %** | OccupancyProcessor → 60s rolling window | 60s |
| **F3 — Age / Gender** | DemographicsProcessor → 5m rolling window | 5m |
| **F4 — Dance Floor** | DanceFloorProcessor (optical flow) | 30s |
| **F5 — Vibe Zones** | VibeEngine rule-based matching | 5m or trigger |

---

## Extending

1. **Add a new CV module** → create `cv-pipeline/src/processors/your_module.py`, inherit `BaseProcessor`, register in `cv-pipeline/src/main.py`.
2. **Add a new signal** → update the processor output schema, add aggregation logic in `signal-service/src/aggregator.py`, expose in `api-server/src/main.py`.
3. **Swap in real models** → replace dummy logic inside `occupancy.py`, `demographics.py`, etc. The interfaces don't change.
4. **Scale out** → run multiple `cv-pipeline` instances sharded by `venue_id`, or move the same definitions to Kubernetes.

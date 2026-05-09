# VibeCheck — Operations Manual

One-command start/stop. Logs live in `./logs/`.

---

## Quick Start

```bash
cd vibecheck-backend
./start-demo.sh
```

Open http://localhost:8000/app/ in your browser.

---

## Stop Everything

```bash
./stop-demo.sh
```

---

## Expose to the Internet (mobile demo)

Open **two separate terminals** and run:

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

## Service Map

| Service | Port | What it does |
|---------|------|-------------|
| FastAPI + Web Player | **8000** | API docs, venue data, signals, static HTML |
| HLS HTTP Server | **8081** | Serves `.m3u8` playlists and `.ts` segments |
| MediaMTX (RTSP router) | **8554** | Ingests cameras / dummy feeds, re-streams as RTSP |
| MediaMTX (native HLS) | **8888** | Optional — HLS straight from MediaMTX |
| Redis | **6379** | Message bus between CV pipeline and signal service |
| CV Pipeline | — | Reads video, runs face blur + occupancy + demographics + dancefloor |
| Signal Service | — | Aggregates rolling windows, runs vibe engine rules |

---

## Logs

```bash
# View all logs
tail -f logs/*.log

# View a specific service
tail -f logs/mediamtx.log
tail -f logs/cv-pipeline.log
tail -f logs/signal-service.log
tail -f logs/api-server.log
tail -f logs/hls-venue-001.log
tail -f logs/hls-venue-002.log
tail -f logs/hls-venue-003.log
```

---

## Health Checks

```bash
# API
curl http://localhost:8000/

# Venue list
curl http://localhost:8000/venues

# Signals for a venue
curl http://localhost:8000/venues/venue-001/signals

# HLS playlist
curl http://localhost:8081/venue-001/index.m3u8

# MediaMTX native HLS (optional)
curl http://localhost:8888/venue-001/index.m3u8
```

---

## Connect a Real CCTV Camera

### 1. Edit `mediamtx/mediamtx.yml`

```yaml
venue-001:
  source: rtsp://192.168.0.108:8080/h264_pcm.sdp
  # comment out runOnInit when using a real camera
  # runOnInit: /opt/homebrew/bin/ffmpeg ...
  # runOnInitRestart: yes
```

### 2. Restart

```bash
./stop-demo.sh && ./start-demo.sh
```

The HLS generator automatically pulls from `rtsp://localhost:8554/venue-001` (which now proxies your real camera). No other files need changing.

---

## Switch a Venue Back to Dummy Feed

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

## Add a New Venue

### 1. `mediamtx/mediamtx.yml`

Add under `paths:`

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

## Restart Just the HLS Generators

If you changed a camera source and don't want to restart everything:

```bash
# Kill existing ffmpeg HLS pullers
pkill -f "ffmpeg.*rtsp://localhost:8554"

# Remove stale segments
rm -f hls/venue-001/*.ts hls/venue-001/*.m3u8

# Restart just this venue's HLS generator
/opt/homebrew/bin/ffmpeg \
  -rtsp_transport tcp -fflags +discardcorrupt \
  -i rtsp://localhost:8554/venue-001 \
  -c:v copy -an \
  -f hls -hls_time 2 -hls_list_size 15 \
  -hls_flags delete_segments+append_list \
  hls/venue-001/index.m3u8
```

---

## Restart Just the CV Pipeline

```bash
pkill -f "python cv-pipeline/src/main.py"
cd vibecheck-backend
source .venv/bin/activate
export PYTHONPATH="api-server/src:cv-pipeline/src:signal-service/src"
export DUMMY_MODE=true
python cv-pipeline/src/main.py &
```

---

## Restart Just the API Server

```bash
pkill -f "uvicorn api-server.src.main:app"
cd vibecheck-backend
source .venv/bin/activate
export PYTHONPATH="api-server/src:cv-pipeline/src:signal-service/src"
uvicorn api-server.src.main:app --host 0.0.0.0 --port 8000 &
```

---

## Common Issues

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

The static file mount hijacked the root. Restart:

```bash
./stop-demo.sh && ./start-demo.sh
```

### ngrok URL changed

ngrok free URLs rotate every restart. Just grab the new one:

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

---

## File Cheat Sheet

| File | What to edit for |
|------|------------------|
| `mediamtx/mediamtx.yml` | Add/remove cameras, change RTSP sources |
| `api-server/src/db.py` | Add venue metadata (name, capacity, location) |
| `cv-pipeline/src/main.py` | Add venue to CV worker registry |
| `signal-service/src/main.py` | Add venue to signal aggregator registry |
| `web-player/index.html` | UI styling, player behaviour |
| `start-demo.sh` | Startup orchestration |
| `stop-demo.sh` | Kill commands |
| `hls_server.py` | HLS HTTP server (CORS, cache headers) |

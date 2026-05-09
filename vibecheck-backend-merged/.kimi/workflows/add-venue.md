# Workflow: Add a New Venue

## Goal
Register a new venue (cafe, bar, or club) so it appears in the API and gets processed.

## Steps

### 1. MediaMTX config

Edit `mediamtx/mediamtx.yml` → add under `paths:`:

```yaml
venue-004:
  source: rtsp://192.168.0.200/stream
  # OR for dummy:
  # source: publisher
  # runOnInit: /opt/homebrew/bin/ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=15 -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://localhost:8554/venue-004
  # runOnInitRestart: yes
```

### 2. Database seed

Edit `api-server/src/db.py` → add to `init_db()`:

```python
VenueORM(
    id="venue-004",
    name="The Blue Door",
    type="bar",
    capacity=150,
    has_dancefloor=True,
    stream_path="venue-004",
    lat=51.5100,
    lon=-0.1000,
),
```

### 3. CV pipeline registry

Edit `cv-pipeline/src/main.py` → add to `VENUES`:

```python
VENUES = [
    # ... existing ...
    {"id": "venue-004", "capacity": 150, "has_dancefloor": True},
]
```

### 4. Signal service registry

Edit `signal-service/src/main.py` → add to `VENUES`:

```python
VENUES = {
    # ... existing ...
    "venue-004": {"capacity": 150, "has_dancefloor": True},
}
```

### 5. HLS directory

```bash
mkdir -p hls/venue-004
```

### 6. Restart

```bash
./stop-demo.sh && ./start-demo.sh
```

### 7. Verify

```bash
curl http://localhost:8000/venues
# Should include venue-004

curl http://localhost:8000/venues/venue-004/signals
# Should return signals (may take 60s for first occupancy)

curl http://localhost:8081/venue-004/index.m3u8
# Should return HLS playlist
```

## Notes

- `stream_path` must match the path name in `mediamtx.yml` exactly.
- `has_dancefloor` controls whether the DanceFloorProcessor runs.
- `capacity` is used for occupancy percentage calculation.
- `type` is one of: `cafe`, `bar`, `club`.

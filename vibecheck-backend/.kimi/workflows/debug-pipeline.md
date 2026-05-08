# Workflow: Debug the CV / Signal Pipeline

## Symptom: Signals are missing or stale

## Diagnostic Steps

### 1. Is the CV pipeline running?

```bash
ps aux | grep "cv-pipeline/src/main.py" | grep -v grep
```

If not running, restart it:
```bash
source .venv/bin/activate
export PYTHONPATH="api-server/src:cv-pipeline/src:signal-service/src"
python cv-pipeline/src/main.py &
```

### 2. Is the CV pipeline producing frames?

```bash
tail -f logs/cv-pipeline.log | grep -E "venue-001|ERROR|failed"
```

Look for:
- `DUMMY MODE: generating synthetic frames` (expected for dummy)
- `Stream opened: rtsp://...` (expected for real camera)
- `Processor X failed` (indicates a bug)

### 3. Is Redis receiving messages?

```bash
redis-cli psubscribe "cv.raw.*"
```

You should see JSON payloads flowing every few seconds.

### 4. Is the signal service subscribing?

```bash
tail -f logs/signal-service.log | grep -E "Flushed|venue-001"
```

You should see `Flushed signals for venue-001` every 60s.

### 5. Is the API receiving POSTs?

```bash
tail -f logs/api-server.log | grep -E "POST /venues"
```

You should see `POST /venues/venue-001/signals HTTP/1.1" 200 OK`.

### 6. Is the API cache populated?

```bash
curl http://localhost:8000/venues/venue-001/signals | python3 -m json.tool
```

If `occupancy` is `null`, the signal service hasn't flushed yet. Wait up to 60 seconds.

### 7. Check individual processor output

Add temporary debug logging in the processor:

```python
def process(self, frame, context):
    result = {...}
    logger.info(f"DEBUG: {result}")
    return result
```

Then `tail -f logs/cv-pipeline.log | grep DEBUG`.

### 8. Is the frame grabber working?

For dummy mode: it always works.
For real camera:
```bash
ffprobe -rtsp_transport tcp -i rtsp://localhost:8554/venue-001
```
If this hangs, MediaMTX is not receiving the camera feed.

## Common Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| No signals at all | CV pipeline crashed | Check logs, fix exception, restart |
| Occupancy always 0 | Processor not registered | Check `build_processors()` |
| Signals stale (>5 min) | Signal service crashed | Restart signal service |
| `null` occupancy | Venue not in signal-service registry | Add to `VENUES` dict |
| JSON serialization error | Processor returned ndarray | Remove ndarray from return dict |
| HLS not playing | ffmpeg not generating segments | Check `ls hls/venue-001/`, restart HLS generator |

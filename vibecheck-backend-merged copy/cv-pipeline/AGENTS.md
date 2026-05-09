# CV Pipeline — Agent Instructions

## What This Service Does

Reads video frames from RTSP streams (or generates synthetic frames in dummy mode), runs a chain of CV processors on each frame, and publishes raw inference outputs to Redis pub/sub.

## Entry Point

```bash
python cv-pipeline/src/main.py
```

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Venue discovery, Redis connection, worker orchestration |
| `src/worker.py` | Per-venue frame loop, processor dispatch, Redis publish |
| `src/processors/base.py` | Abstract interface ALL processors must inherit |
| `src/processors/anonymizer.py` | Privacy gate — blurs faces before any output |
| `src/processors/occupancy.py` | Head counting (HOG placeholder) |
| `src/processors/demographics.py` | Age/gender dummy |
| `src/processors/dancefloor.py` | Optical flow energy detector |
| `src/utils/frame_grabber.py` | RTSP/HLS → OpenCV frame reader |

## Constraints

1. **Processors run in order.** Anonymizer is always first. Then occupancy, demographics, dancefloor (if enabled). Your processor goes at the end.

2. **Never publish ndarrays to Redis.** JSON serialization will crash. Extract scalar values only.

3. **Respect required_fps.** The worker throttles each processor independently. If you set `required_fps = 0.5`, your processor runs at most once every 2 seconds.

4. **Dummy mode must always work.** Every processor must return sensible dummy data when `DUMMY_MODE=true`. This lets frontend devs work without cameras.

5. **Frame format is BGR.** OpenCV standard. Shape `(H, W, 3)`, dtype `uint8`.

6. **RTSP reconnection.** If the stream drops, the frame grabber waits 1s and reconnects. Your processor should handle missing frames gracefully.

## Adding a Processor

See `.kimi/workflows/add-cv-processor.md` for the full workflow.

Quick version:
1. Create `src/processors/my_processor.py`
2. Inherit `BaseProcessor`
3. Implement `process(frame, context) -> dict`
4. Add to `src/processors/__init__.py`
5. Add to `src/worker.py` → `build_processors()`

## Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `MEDIAMTX_URL` | `http://localhost:8888` | Not used for RTSP ingest (we use `rtsp://localhost:8554`) |
| `DUMMY_MODE` | `true` | Use synthetic frames |

## Testing

```bash
source ../.venv/bin/activate
export PYTHONPATH="../api-server/src:../cv-pipeline/src:../signal-service/src"
python -c "from processors.occupancy import OccupancyProcessor; print('OK')"
```

## Common Issues

- **Import errors:** Make sure `PYTHONPATH` includes all three `src/` directories.
- **Redis connection refused:** Start Redis first (`redis-server`).
- **Stream not opening:** Check MediaMTX is running and the path exists in `mediamtx.yml`.
- **High CPU:** Reduce `required_fps` or resize frames early in `process()`.

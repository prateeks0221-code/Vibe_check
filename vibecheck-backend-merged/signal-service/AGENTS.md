# Signal Service — Agent Instructions

## What This Service Does

Subscribes to Redis pub/sub for raw CV events, maintains rolling-window aggregators per venue, runs the vibe engine rule matcher, and pushes aggregated signals to the API server via REST POST.

## Entry Point

```bash
python signal-service/src/main.py
```

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Redis subscriber, flush cadence, API client caller |
| `src/aggregator.py` | Rolling windows (60s / 5m / 30s), per-venue state |
| `src/vibe_engine.py` | Rule-based descriptor matching (F5) |
| `src/api_client.py` | Thin wrapper around `requests.post()` |

## Constraints

1. **Flush cadences are sacred.**
   - Occupancy: 60s
   - Demographics: 5m (300s)
   - Dance floor: 30s
   - New signals: pick a sensible cadence and document it

2. **Vibe engine runs on demographics or dancefloor updates, OR every 5 minutes.**
   Don't run it more often — it's expensive and doesn't need to be real-time.

3. **Historical baselines are stored per-venue.**
   `VenueAggregator.dancefloor_baseline` starts at 25.0 and should be calibrated over 30 days per venue. For MVP, leave it at the default.

4. **Never block the Redis subscriber.**
   The `for message in pubsub.listen()` loop must never block. All heavy work (API POST, vibe engine) should be fast or offloaded to threads. For MVP, keep it simple.

5. **Venue registry is hardcoded.**
   `VENUES` dict in `main.py`. When adding a venue, update this dict.

## Adding a New Signal

See `.kimi/workflows/add-signal.md` for the full workflow.

Quick version:
1. Add window buffer in `aggregator.py`
2. Add `ingest()` branch
3. Add `compute_*()` method
4. Add flush cadence in `main.py`
5. Add to signals payload in `main.py`

## Vibe Engine

Descriptors are hardcoded in `vibe_engine.py` → `DEFAULT_DESCRIPTORS`.

To add a descriptor, add a dict with `label` and `conditions`. See `.kimi/skills/vibe-descriptor.md`.

## Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `API_SERVER_URL` | `http://localhost:8000` | FastAPI base URL |

## Testing

```bash
source ../.venv/bin/activate
export PYTHONPATH="../api-server/src:../cv-pipeline/src:../signal-service/src"
python -c "from aggregator import VenueAggregator; a = VenueAggregator('test', 100); print('OK')"
```

## Common Issues

- **No signals appearing:** Check that the venue ID matches between CV pipeline, signal service, and API.
- **Stale signals:** Check flush cadence. Check that the processor name matches in `cadence` dict.
- **Vibe zones empty:** Check that descriptors have matching conditions for current signal values.

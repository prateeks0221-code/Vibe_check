# Rule 07: Testing

## Philosophy

- **Integration over unit tests for CV.** The real test is: does the signal appear at `/venues/{id}/signals`?
- **Unit tests for pure functions.** Aggregators, vibe engine rules, Pydantic validators.
- **Manual testing is acceptable for MVP.** Automated E2E tests are post-MVP.

## Running Tests

```bash
cd vibecheck-backend
source .venv/bin/activate
pytest
```

If pytest is not installed:
```bash
pip install pytest pytest-asyncio
```

## Test File Layout

```
cv-pipeline/tests/
    test_processors.py
signal-service/tests/
    test_aggregator.py
    test_vibe_engine.py
api-server/tests/
    test_api.py
```

## Processor Test Template

```python
import numpy as np
from processors.occupancy import OccupancyProcessor

def test_occupancy_processor():
    proc = OccupancyProcessor()
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    context = {"venue_id": "test", "timestamp": 0.0}
    result = proc.process(frame, context)
    assert "head_count" in result
    assert isinstance(result["head_count"], int)
```

## API Test Template

```python
from fastapi.testclient import TestClient
from api_server.src.main import app

client = TestClient(app)

def test_list_venues():
    response = client.get("/venues")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Vibe Engine Test Template

```python
from signal_service.src.vibe_engine import VibeEngine

def test_vibe_engine_peak_time():
    engine = VibeEngine()
    zones = engine.evaluate(
        occupancy={"percentage": 85},
        demographics={"primary_age_bracket": "25-34"},
        dancefloor={"state": "Active"},
        hour=22,
    )
    labels = [z["label"] for z in zones]
    assert "Peak time" in labels
```

## Manual Testing Checklist

Before claiming a feature is done:

- [ ] `./start-demo.sh` runs without errors
- [ ] `http://localhost:8000/venues` returns the venue
- [ ] `http://localhost:8000/venues/{id}/signals` returns the new signal
- [ ] The web player shows the new signal card
- [ ] `./stop-demo.sh` kills all processes
- [ ] `./start-demo.sh` again works cleanly

## Logging for Debug

Add `logger.debug()` liberally during development. Set log level:

```bash
LOG_LEVEL=debug ./start-demo.sh
```

(Modify `start-demo.sh` to export `LOG_LEVEL` if needed.)

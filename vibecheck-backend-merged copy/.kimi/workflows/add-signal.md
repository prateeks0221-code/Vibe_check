# Workflow: Add a New Signal (End-to-End)

## Goal
Add a completely new signal type from processor → aggregation → API → frontend.

## Overview

This touches 5 files:
1. `cv-pipeline/src/processors/` — compute the raw signal
2. `signal-service/src/aggregator.py` — rolling window
3. `signal-service/src/main.py` — flush cadence + push to API
4. `api-server/src/models.py` — Pydantic schema
5. `web-player/index.html` — UI card

## Steps

### 1. Create the processor

Follow `.kimi/workflows/add-cv-processor.md` for processor creation.

### 2. Add aggregation window

In `signal-service/src/aggregator.py`:

```python
class VenueAggregator:
    def __init__(self, venue_id: str, capacity: int):
        # ... existing ...
        self.my_signal = WindowBuffer(window_seconds=60)

    def ingest(self, processor_name: str, payload: dict):
        # ... existing ...
        elif processor_name == "my_signal":
            self.my_signal.add(ts, payload)

    def compute_my_signal(self) -> Optional[dict]:
        if not self.my_signal._items:
            return None
        # aggregate however you want
        latest = self.my_signal.latest()
        return {
            "value": latest.get("value", 0),
            "label": latest.get("label", "unknown"),
        }
```

### 3. Register flush cadence

In `signal-service/src/main.py`:

```python
cadence = {
    "occupancy": 60,
    "demographics": 300,
    "dancefloor": 30,
    "my_signal": 60,  # <-- add
}.get(processor_name, 60)
```

### 4. Add to flush payload

In `signal-service/src/main.py`:

```python
signals = {
    "venue_id": venue_id,
    "timestamp": now,
    "occupancy": agg.compute_occupancy(),
    "demographics": agg.compute_demographics(),
    "dancefloor": agg.compute_dancefloor() if VENUES[venue_id]["has_dancefloor"] else None,
    "my_signal": agg.compute_my_signal(),  # <-- add
}
```

### 5. Add Pydantic schema

In `api-server/src/models.py`:

```python
class MySignal(BaseModel):
    value: int
    label: str

class VenueSignals(BaseModel):
    # ... existing ...
    my_signal: Optional[MySignal] = None
```

### 6. Add frontend card

In `web-player/index.html` → `renderSignals()`:

```javascript
if (data.my_signal) {
    const ms = data.my_signal;
    html += `
        <div class="card">
            <h2>My Signal</h2>
            <div class="pills">
                <div class="pill">${ms.label}</div>
            </div>
            <p class="muted">Value: ${ms.value}</p>
        </div>
    `;
}
```

### 7. Test

```bash
./stop-demo.sh && ./start-demo.sh
curl http://localhost:8000/venues/venue-001/signals | python3 -m json.tool
```

Verify `my_signal` appears in the JSON response.

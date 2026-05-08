# Workflow: Add a New CV Processor

## Goal
Add a new computer vision module (e.g., bar queue detection, smoking area occupancy) to the pipeline.

## Prerequisites
- Read `.kimi/rules/03-cv-processors.md`
- Know the processor's required_fps and output schema

## Steps

### 1. Create the processor file

```bash
touch cv-pipeline/src/processors/my_processor.py
```

Inherit `BaseProcessor`. Implement `process()`. Return a JSON-serializable dict.

### 2. Export it

Add to `cv-pipeline/src/processors/__init__.py`:

```python
from processors.my_processor import MyProcessor
__all__ = [..., "MyProcessor"]
```

### 3. Register in the worker

Edit `cv-pipeline/src/worker.py` → `build_processors()`:

```python
from processors import ..., MyProcessor

def build_processors(venue: dict):
    procs = [Anonymizer(), OccupancyProcessor(), DemographicsProcessor()]
    if venue.get("has_dancefloor"):
        procs.append(DanceFloorProcessor())
    procs.append(MyProcessor())  # <-- add this
    return procs
```

### 4. Register flush cadence in signal service

Edit `signal-service/src/main.py`:

```python
cadence = {
    "occupancy": 60,
    "demographics": 300,
    "dancefloor": 30,
    "my_processor": 60,  # <-- add this
}.get(processor_name, 60)
```

### 5. Add aggregation logic

Edit `signal-service/src/aggregator.py`:

```python
class VenueAggregator:
    def __init__(...):
        # ... existing windows ...
        self.my_processor = WindowBuffer(window_seconds=60)

    def ingest(self, processor_name: str, payload: dict):
        # ... existing ...
        elif processor_name == "my_processor":
            self.my_processor.add(ts, payload.get("my_value", 0))

    def compute_my_processor(self):
        return {"my_value": int(self.my_processor.mean(default=0))}
```

### 6. Add to API model

Edit `api-server/src/models.py`:

```python
class MyProcessorSignal(BaseModel):
    my_value: int

class VenueSignals(BaseModel):
    # ... existing fields ...
    my_processor: Optional[MyProcessorSignal] = None
```

### 7. Flush in signal service

Edit `signal-service/src/main.py`:

```python
signals = {
    "venue_id": venue_id,
    "timestamp": now,
    "occupancy": agg.compute_occupancy(),
    "demographics": agg.compute_demographics(),
    "dancefloor": agg.compute_dancefloor() if VENUES[venue_id]["has_dancefloor"] else None,
    "my_processor": agg.compute_my_processor(),  # <-- add this
}
```

### 8. Add frontend card

Edit `web-player/index.html` → `renderSignals()`:

```javascript
if (data.my_processor) {
    const mp = data.my_processor;
    html += `
        <div class="card">
            <h2>My Processor</h2>
            <div class="occupancy">
                <span class="pct">${mp.my_value}</span>
            </div>
        </div>
    `;
}
```

### 9. Test

```bash
./stop-demo.sh && ./start-demo.sh
curl http://localhost:8000/venues/venue-001/signals
# Verify my_processor appears in the response
```

### 10. Document

Add the new signal to README.md → PRD Feature Mapping table.

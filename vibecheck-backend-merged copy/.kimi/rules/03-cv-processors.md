# Rule 03: CV Processor Development

## The Processor Interface

Every CV module **must** inherit from `BaseProcessor` and implement:

```python
class BaseProcessor(ABC):
    name: str = "base"
    required_fps: float = 1.0

    @abstractmethod
    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        ...
```

## Creating a New Processor

1. Create `cv-pipeline/src/processors/your_processor.py`
2. Inherit `BaseProcessor`
3. Set `name` and `required_fps`
4. Implement `process()`
5. Import and register in `cv-pipeline/src/worker.py` → `build_processors()`

## `process()` Contract

### Input
- `frame`: `np.ndarray` in BGR format (OpenCV standard), shape `(H, W, 3)`
- `context`: dict with keys `venue_id` (str), `timestamp` (float), optionally `zone`, `camera_id`

### Output
- Return a **JSON-serializable dict**. Keys are up to you.
- **Do NOT include `np.ndarray` in the return dict.** It will crash JSON serialization.
- Include `venue_id` and `timestamp` in the output for downstream aggregation.

### Throttling
The worker respects `required_fps` automatically. If you set `required_fps = 0.5`, the worker calls your processor at most once every 2 seconds.

## Example: Minimal Processor

```python
"""Detects bar queues."""
import numpy as np
import cv2
from typing import Any, Dict
from processors.base import BaseProcessor


class BarQueueProcessor(BaseProcessor):
    name = "bar_queue"
    required_fps = 0.5

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        # Dummy: count people in the bottom 30% of the frame
        h, w = frame.shape[:2]
        roi = frame[int(h * 0.7):, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        # ... real detection logic here ...
        queue_count = 5  # placeholder

        return {
            "queue_count": queue_count,
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
        }
```

## Registration

In `cv-pipeline/src/worker.py`:

```python
def build_processors(venue: dict):
    procs = [
        Anonymizer(),
        OccupancyProcessor(),
        DemographicsProcessor(),
    ]
    if venue.get("has_dancefloor"):
        procs.append(DanceFloorProcessor())
    # Add your processor here
    procs.append(BarQueueProcessor())
    return procs
```

## Signal-Service Registration

Add the processor name to `signal-service/src/main.py` → `cadence` dict so it knows how often to flush:

```python
cadence = {
    "occupancy": 60,
    "demographics": 300,
    "dancefloor": 30,
    "bar_queue": 60,  # <-- add this
}.get(processor_name, 60)
```

Then add aggregation logic in `signal-service/src/aggregator.py`:

```python
def ingest(self, processor_name: str, payload: dict):
    # ... existing ...
    elif processor_name == "bar_queue":
        self.bar_queue.add(ts, payload.get("queue_count", 0))

def compute_bar_queue(self):
    mean_queue = self.bar_queue.mean(default=0)
    return {"queue_count": int(mean_queue)}
```

And add to the flush in `signal-service/src/main.py`:

```python
signals = {
    # ... existing ...
    "bar_queue": agg.compute_bar_queue(),
}
```

## Dummy Mode

If the processor can't run without a real model, make it return sensible dummy data when `DUMMY_MODE=true`:

```python
import os

class BarQueueProcessor(BaseProcessor):
    def process(self, frame, context):
        if os.getenv("DUMMY_MODE", "false").lower() == "true":
            return {"queue_count": random.randint(0, 10), ...}
        # real logic ...
```

## Performance

- Resize frames early if you don't need full resolution.
- Use `-c:v copy` in HLS generators. Never re-encode video unless necessary.
- Target <50ms per frame per processor at the required_fps.

## Privacy

- The `Anonymizer` processor runs first and blurs faces.
- Your processor receives the **already-anonymized** frame.
- Never attempt to de-anonymize or run facial recognition.

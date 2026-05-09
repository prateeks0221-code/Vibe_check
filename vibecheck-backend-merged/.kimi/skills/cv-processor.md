# Skill: CV Processor Template

## Copy-Paste Template

```python
"""Short description of what this processor does."""
import os
import numpy as np
import cv2
from typing import Any, Dict
from processors.base import BaseProcessor


class MyProcessor(BaseProcessor):
    """
    Longer description.
    Production swap: mention what real model replaces this.
    """

    name = "my_processor"
    required_fps = 1.0

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        if os.getenv("DUMMY_MODE", "false").lower() == "true":
            return self._dummy(context)

        # Real logic here
        result = self._detect(frame)

        return {
            "value": result,
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
        }

    def _dummy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        import random
        return {
            "value": random.randint(0, 100),
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
        }

    def _detect(self, frame: np.ndarray) -> int:
        # Your real detection logic
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # ...
        return 42
```

## Registration Checklist

- [ ] File created at `cv-pipeline/src/processors/my_processor.py`
- [ ] Added to `cv-pipeline/src/processors/__init__.py`
- [ ] Added to `cv-pipeline/src/worker.py` → `build_processors()`
- [ ] Added flush cadence in `signal-service/src/main.py`
- [ ] Added aggregation in `signal-service/src/aggregator.py`
- [ ] Added Pydantic model in `api-server/src/models.py`
- [ ] Added frontend card in `web-player/index.html`
- [ ] Tested with `./start-demo.sh`

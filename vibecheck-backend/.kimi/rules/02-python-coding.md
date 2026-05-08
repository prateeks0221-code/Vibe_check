# Rule 02: Python Coding Standards

## Style

- **Black-compatible formatting.** 4-space indentation. Max line length 100.
- **Type hints everywhere.** Use `from typing import Dict, List, Optional, Any`.
- **Docstrings for every module, class, and public function.** Google-style.

## Imports

Order: stdlib → third-party → local. Group with blank lines.

```python
import os
import json
from typing import Dict, List, Optional

import redis
import numpy as np
import cv2

from processors.base import BaseProcessor
```

## Error Handling

- Catch specific exceptions. Never bare `except:`.
- Log exceptions with `logging.exception()` (includes traceback).
- Graceful degradation: if a processor fails, log and continue. Don't crash the worker.

```python
try:
    result = proc.process(frame, context)
except Exception:
    logger.exception(f"[{venue_id}] Processor {proc.name} failed")
    continue
```

## Async

- FastAPI endpoints: use `async def` when doing I/O (DB, Redis, HTTP).
- CV pipeline and signal service: sync only. These are CPU-bound workers.
- Never mix asyncio and threading in the same service.

## Environment Variables

```python
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DUMMY_MODE = os.getenv("DUMMY_MODE", "false").lower() == "true"
```

Always provide a sensible default so `./start-demo.sh` works without extra env setup.

## Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
```

Use `logger.info()` for startup/shutdown, `logger.warning()` for recoverable issues, `logger.exception()` for errors.

## File I/O

- Use `pathlib.Path` over `os.path`.
- Use context managers (`with open(...) as f:`).
- Don't write to files outside the project directory.

## NumPy / OpenCV

- Always pass frames as `np.ndarray` (BGR, OpenCV standard).
- Use `.copy()` if you modify a frame in-place.
- Never serialize `np.ndarray` directly to JSON (causes `TypeError`).

## Configuration Files

- YAML: use plain PyYAML (already installed via uvicorn[standard]).
- JSON: use `json` stdlib. Pretty-print with `indent=2` when writing configs.
- Never commit secrets to YAML. Use env vars.

"""Per-venue CV worker: grabs frames, runs processors, publishes raw events."""
import time
import json
import logging
from typing import List
import redis
from processors.base import BaseProcessor
from utils.frame_grabber import FrameGrabber

logger = logging.getLogger(__name__)


class VenueWorker:
    def __init__(
        self,
        venue_id: str,
        stream_url: str,
        processors: List[BaseProcessor],
        redis_client: redis.Redis,
    ):
        self.venue_id = venue_id
        self.stream_url = stream_url
        self.processors = processors
        self.redis = redis_client
        self.grabber = FrameGrabber(stream_url, venue_id, fps_target=5.0)

    def run(self):
        logger.info(f"[{self.venue_id}] Worker starting with {len(self.processors)} processors")
        # Track last run time per processor for fps throttling
        last_run = {p.name: 0.0 for p in self.processors}

        for frame in self.grabber.frames():
            ts = time.time()
            context = {
                "venue_id": self.venue_id,
                "timestamp": ts,
            }

            for proc in self.processors:
                if ts - last_run[proc.name] < (1.0 / proc.required_fps):
                    continue
                try:
                    result = proc.process(frame, context)
                    if result:
                        self._publish(proc.name, result)
                    last_run[proc.name] = ts
                except Exception:
                    logger.exception(f"[{self.venue_id}] Processor {proc.name} failed")

    def _publish(self, processor_name: str, payload: dict):
        channel = f"cv.raw.{self.venue_id}.{processor_name}"
        self.redis.publish(channel, json.dumps(payload))

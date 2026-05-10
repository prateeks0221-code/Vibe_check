"""Per-venue CV worker: grab thread owns video frames; inference thread owns YOLO.

Grab thread publishes raw JPEG at full fps → smooth browser video.
Inference thread publishes detection JSON at YOLO speed → overlay data.
Both over MQTT so browser always has fresh video even when GPU is busy.
"""
import os
import time
import json
import logging
import threading
from typing import List, Optional

import cv2
import numpy as np
import redis
import paho.mqtt.client as mqtt_lib

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

        max_fps = max((p.required_fps for p in processors), default=5.0)
        self.grabber = FrameGrabber(stream_url, venue_id, fps_target=max_fps)
        self._mqtt = self._init_mqtt()

        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._frame_event = threading.Event()

    def _init_mqtt(self) -> mqtt_lib.Client:
        client = mqtt_lib.Client()
        host = os.environ.get("MQTT_HOST", "vc_mosquitto")
        try:
            client.connect(host, 1883, keepalive=60)
            client.loop_start()
            logger.info(f"[{self.venue_id}] MQTT connected → {host}:1883")
        except Exception as exc:
            logger.warning(f"[{self.venue_id}] MQTT unavailable ({exc})")
        return client

    def run(self):
        logger.info(
            f"[{self.venue_id}] Worker starting — {len(self.processors)} processors, "
            f"grabber fps={self.grabber.fps_target}"
        )
        inf = threading.Thread(
            target=self._inference_loop, daemon=True, name=f"inf-{self.venue_id}"
        )
        inf.start()

        # Grab thread: publish fresh JPEG every frame → smooth video at full fps
        for frame in self.grabber.frames():
            with self._frame_lock:
                self._latest_frame = frame.copy()
            self._frame_event.set()
            self._publish_frame(frame)   # ← video at grab fps, independent of YOLO

    # ── Inference thread ──────────────────────────────────────────────────────

    def _inference_loop(self):
        """Runs processors on latest frame. Decoupled from grab — never blocks video."""
        last_run = {p.name: 0.0 for p in self.processors}
        while True:
            got = self._frame_event.wait(timeout=1.0)
            self._frame_event.clear()
            if not got:
                continue

            with self._frame_lock:
                frame = self._latest_frame
            if frame is None:
                continue

            ts = time.time()
            context = {"venue_id": self.venue_id, "timestamp": ts}

            for proc in self.processors:
                if ts - last_run[proc.name] < (1.0 / proc.required_fps):
                    continue
                try:
                    result = proc.process(frame, context)
                    if result:
                        self._publish_redis(proc.name, result)
                        if proc.name == "person_detector":
                            context["detections"] = result.get("detections", [])
                            self._publish_detections(result)
                        if proc.name == "occupancy":
                            context["occupancy"] = result.get("head_count", 0)
                    last_run[proc.name] = ts
                except Exception:
                    logger.exception(f"[{self.venue_id}] Processor {proc.name} failed")

    # ── Publishers ────────────────────────────────────────────────────────────

    def _publish_redis(self, processor_name: str, payload: dict):
        channel = f"cv.raw.{self.venue_id}.{processor_name}"
        self.redis.publish(channel, json.dumps(payload))

    def _publish_frame(self, frame: np.ndarray):
        """Resize to 640×360, JPEG Q70, push to MQTT → browser video."""
        small = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)
        ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ok:
            try:
                self._mqtt.publish(f"vibecheck/{self.venue_id}/frame", buf.tobytes(), qos=0)
            except Exception:
                pass

    def _publish_detections(self, result: dict):
        """Push detection JSON to MQTT — browser draws overlay from this."""
        payload = {
            "detections": result.get("detections", []),
            "paths": result.get("paths", {}),
            "frame_w": result.get("frame_w"),
            "frame_h": result.get("frame_h"),
            "person_count": result.get("person_count"),
        }
        try:
            self._mqtt.publish(
                f"vibecheck/{self.venue_id}/detections",
                json.dumps(payload),
                qos=0,
            )
        except Exception:
            pass

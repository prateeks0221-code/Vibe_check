"""Grab frames from HLS or RTSP sources using OpenCV."""
import os
import time
import logging
import numpy as np
import cv2
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


class FrameGrabber:
    def __init__(self, source_url: str, venue_id: str, fps_target: float = 5.0):
        self.source_url = source_url
        self.venue_id = venue_id
        self.fps_target = fps_target
        self.frame_time = 1.0 / fps_target
        self._cap: Optional[cv2.VideoCapture] = None
        self._dummy_mode = os.getenv("DUMMY_MODE", "true").lower() == "true"

    def _open(self):
        if self._dummy_mode:
            logger.info(f"[{self.venue_id}] DUMMY MODE: generating synthetic frames")
            return
        self._cap = cv2.VideoCapture(self.source_url)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open stream: {self.source_url}")
        logger.info(f"[{self.venue_id}] Stream opened: {self.source_url}")

    def _generate_dummy(self) -> np.ndarray:
        """Create a synthetic 720p frame with moving shapes."""
        t = time.time()
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        # background gradient
        frame[:, :, 0] = int(20 + 10 * np.sin(t))
        frame[:, :, 1] = int(20 + 10 * np.cos(t * 0.7))
        frame[:, :, 2] = 40
        # moving circles = "people"
        for i in range(15):
            cx = int(640 + 400 * np.sin(t * 0.5 + i))
            cy = int(360 + 250 * np.cos(t * 0.3 + i * 1.1))
            color = (0, 180, 220) if i % 2 == 0 else (220, 180, 0)
            cv2.circle(frame, (cx % 1280, cy % 720), 25, color, -1)
        # text overlay
        cv2.putText(frame, f"DUMMY {self.venue_id}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame

    def frames(self) -> Iterator[np.ndarray]:
        self._open()
        while True:
            t0 = time.time()
            if self._dummy_mode:
                yield self._generate_dummy()
            else:
                ret, frame = self._cap.read()
                if not ret:
                    logger.warning(f"[{self.venue_id}] Frame read failed, reconnecting...")
                    time.sleep(1)
                    self._open()
                    continue
                yield frame
            # throttle to target fps
            elapsed = time.time() - t0
            sleep = self.frame_time - elapsed
            if sleep > 0:
                time.sleep(sleep)

    def release(self):
        if self._cap:
            self._cap.release()

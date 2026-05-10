"""Grab frames from RTSP/HLS sources — always delivers the freshest frame.

Key design: background thread continuously reads from the cap so the buffer
never accumulates stale frames. Worker calls latest_frame() and gets the most
recent decoded frame without delay.
"""
import os
import time
import logging
import threading
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

        # Background reader state
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_reader = threading.Event()

    # ── Internal: background reader ──────────────────────────────────────────

    def _open_cap(self) -> cv2.VideoCapture:
        while True:
            cap = cv2.VideoCapture(self.source_url)
            # Minimize internal buffer so we always get the latest frame
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if cap.isOpened():
                logger.info(f"[{self.venue_id}] Stream opened: {self.source_url}")
                return cap
            cap.release()
            logger.warning(f"[{self.venue_id}] Stream unavailable, retry in 5s")
            time.sleep(5)

    def _reader_loop(self):
        """Runs in background thread: continuously reads frames, keeps only latest."""
        cap = self._open_cap()
        fail_streak = 0
        while not self._stop_reader.is_set():
            ret, frame = cap.read()
            if not ret:
                fail_streak += 1
                if fail_streak >= 10:
                    logger.warning(f"[{self.venue_id}] Reconnecting after {fail_streak} failures")
                    cap.release()
                    cap = self._open_cap()
                    fail_streak = 0
                time.sleep(0.05)
                continue
            fail_streak = 0
            with self._frame_lock:
                self._latest_frame = frame
        cap.release()

    def _start_reader(self):
        self._stop_reader.clear()
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True, name=f"grabber-{self.venue_id}"
        )
        self._reader_thread.start()

    def _open(self):
        if self._dummy_mode:
            logger.info(f"[{self.venue_id}] DUMMY MODE: generating synthetic frames")
            return
        self._start_reader()
        # Wait until at least one frame is available
        deadline = time.time() + 30
        while self._latest_frame is None and time.time() < deadline:
            time.sleep(0.1)

    # ── Dummy frame generator ─────────────────────────────────────────────────

    def _generate_dummy(self) -> np.ndarray:
        t = time.time()
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[:, :, 0] = int(20 + 10 * np.sin(t))
        frame[:, :, 1] = int(20 + 10 * np.cos(t * 0.7))
        frame[:, :, 2] = 40
        for i in range(15):
            cx = int(640 + 400 * np.sin(t * 0.5 + i))
            cy = int(360 + 250 * np.cos(t * 0.3 + i * 1.1))
            color = (0, 180, 220) if i % 2 == 0 else (220, 180, 0)
            cv2.circle(frame, (cx % 1280, cy % 720), 25, color, -1)
        cv2.putText(frame, f"DUMMY {self.venue_id}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame

    # ── Public API ────────────────────────────────────────────────────────────

    def frames(self) -> Iterator[np.ndarray]:
        self._open()
        while True:
            t0 = time.time()

            if self._dummy_mode:
                yield self._generate_dummy()
            else:
                with self._frame_lock:
                    frame = self._latest_frame
                if frame is None:
                    time.sleep(0.05)
                    continue
                yield frame.copy()

            # Throttle to target fps — background thread keeps draining during sleep
            elapsed = time.time() - t0
            sleep = self.frame_time - elapsed
            if sleep > 0:
                time.sleep(sleep)

    def release(self):
        self._stop_reader.set()
        if self._reader_thread:
            self._reader_thread.join(timeout=2)

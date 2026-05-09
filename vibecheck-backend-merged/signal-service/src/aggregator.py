"""Rolling-window aggregators for occupancy, demographics, dance floor."""
from collections import deque
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class WindowBuffer:
    window_seconds: float
    _items: deque = field(default_factory=deque)

    def add(self, timestamp: float, value):
        self._items.append((timestamp, value))
        self._prune(timestamp)

    def _prune(self, now: float):
        cutoff = now - self.window_seconds
        while self._items and self._items[0][0] < cutoff:
            self._items.popleft()

    def latest(self, default=None):
        return self._items[-1][1] if self._items else default

    def mean(self, default=0.0):
        if not self._items:
            return default
        values = [v for _, v in self._items]
        return sum(values) / len(values)

    def mode(self, default=None):
        if not self._items:
            return default
        from collections import Counter
        values = [v for _, v in self._items]
        return Counter(values).most_common(1)[0][0]

    def proportion(self, key_fn, default=None):
        if not self._items:
            return default
        from collections import Counter
        values = [key_fn(v) for _, v in self._items]
        total = len(values)
        return {k: round(v / total * 100) for k, v in Counter(values).items()}


class VenueAggregator:
    """Holds all rolling windows for a single venue."""

    def __init__(self, venue_id: str, capacity: int):
        self.venue_id = venue_id
        self.capacity = capacity
        self.occupancy = WindowBuffer(window_seconds=60)
        self.demographics = WindowBuffer(window_seconds=300)
        self.dancefloor = WindowBuffer(window_seconds=30)
        # Historical baseline for dance floor normalisation (calibrated over 30 days)
        self.dancefloor_baseline = 25.0  # dummy initial value

    def ingest(self, processor_name: str, payload: dict):
        ts = payload.get("timestamp", time.time())
        if processor_name == "occupancy":
            self.occupancy.add(ts, payload.get("head_count", 0))
        elif processor_name == "demographics":
            self.demographics.add(ts, payload)
        elif processor_name == "dancefloor":
            self.dancefloor.add(ts, payload.get("energy_score", 0))

    def compute_occupancy(self) -> Optional[dict]:
        mean_heads = self.occupancy.mean(default=0)
        if mean_heads == 0:
            return None
        pct = int((mean_heads / self.capacity) * 100) if self.capacity else 0
        if pct <= 30:
            label = "Quiet"
        elif pct <= 60:
            label = "Getting There"
        elif pct <= 85:
            label = "Busy"
        else:
            label = "Packed"
        return {
            "percentage": pct,
            "label": label,
            "head_count": int(mean_heads),
            "capacity": self.capacity,
        }

    def compute_demographics(self) -> Optional[dict]:
        if not self.demographics._items:
            return None
        # Aggregate age brackets across frames
        primary_counter = {}
        male_sum = 0
        n = len(self.demographics._items)
        for _, p in self.demographics._items:
            primary = p.get("primary_age_bracket")
            if primary:
                primary_counter[primary] = primary_counter.get(primary, 0) + 1
            male_sum += p.get("male_presenting_pct", 50)

        primary_age = max(primary_counter, key=primary_counter.get) if primary_counter else "Unknown"
        male_avg = int(male_sum / n)
        return {
            "primary_age_bracket": primary_age,
            "male_presenting_pct": male_avg,
            "female_presenting_pct": 100 - male_avg,
        }

    def compute_dancefloor(self) -> Optional[dict]:
        score = self.dancefloor.mean(default=0)
        if score == 0:
            return None
        # Normalise against baseline
        normalised = int((score / max(self.dancefloor_baseline, 1)) * 50)
        normalised = min(100, max(0, normalised))
        if normalised < 15:
            state = "Dead"
        elif normalised < 40:
            state = "Warming Up"
        elif normalised < 70:
            state = "Active"
        else:
            state = "Raging"
        return {
            "energy_score": normalised,
            "raw_score": int(score),
            "state": state,
        }

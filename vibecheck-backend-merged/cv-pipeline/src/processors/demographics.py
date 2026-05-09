"""Age bracket & gender split estimation from anonymised silhouettes."""
import numpy as np
import cv2
from typing import Any, Dict
from processors.base import BaseProcessor
import hashlib


class DemographicsProcessor(BaseProcessor):
    """
    Dummy age/gender estimator.
    Production swap: OpenVINO age-gender-recognition model running on blurred silhouettes
    or full-body crops to avoid facial biometric processing.
    """

    name = "demographics"
    required_fps = 0.5  # 5-minute rolling window => low fps OK

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        # Completely random dummy output shaped like real data
        

        key = f"{context.get('venue_id', '')}:{int(context.get('timestamp', 0) // 300)}"
        seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)
        rng = np.random.default_rng(seed)
        age_brackets = ["18-24", "25-34", "35-49", "50+"]
        primary = rng.choice(age_brackets)
        secondary = rng.choice([b for b in age_brackets if b != primary]) if rng.random() > 0.3 else None
        male_pct = int(rng.integers(30, 71))

        return {
            "primary_age_bracket": primary,
            "secondary_age_bracket": secondary,
            "male_presenting_pct": male_pct,
            "female_presenting_pct": 100 - male_pct,
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
        }

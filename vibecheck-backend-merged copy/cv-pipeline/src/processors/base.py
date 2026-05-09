"""Abstract base for all CV processors."""
from abc import ABC, abstractmethod
from typing import Any, Dict
import numpy as np


class BaseProcessor(ABC):
    """Every CV module inherits this."""

    name: str = "base"
    required_fps: float = 1.0  # how often this processor needs frames

    @abstractmethod
    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            frame: BGR image (OpenCV standard)
            context: metadata dict with keys like venue_id, camera_id, timestamp
        Returns:
            typed dict of inference outputs
        """
        ...

    def load_model(self, model_path: str):
        """Override if your processor needs a weights file."""
        pass

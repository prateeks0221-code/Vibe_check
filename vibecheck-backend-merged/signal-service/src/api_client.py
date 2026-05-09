"""Push aggregated signals to the API server."""
import os
import json
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

API_BASE = os.getenv("API_SERVER_URL", "http://localhost:8000")


class ApiClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")

    def post_signals(self, venue_id: str, payload: dict):
        url = f"{self.base_url}/venues/{venue_id}/signals"
        try:
            r = requests.post(url, json=payload, timeout=5)
            r.raise_for_status()
        except requests.RequestException as exc:
            logger.warning(f"Failed to push signals for {venue_id}: {exc}")

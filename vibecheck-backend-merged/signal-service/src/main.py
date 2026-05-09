"""Signal service entrypoint: subscribes to Redis, aggregates, runs vibe engine."""
import os
import time
import json
import logging
from datetime import datetime
from threading import Thread
import redis
from aggregator import VenueAggregator
from vibe_engine import VibeEngine
from api_client import ApiClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
API_SERVER_URL = os.getenv("API_SERVER_URL", "http://localhost:8000")

# Venue registry (load from DB in production)
VENUES = {
    "venue-001": {"capacity": 120, "has_dancefloor": True},
    "venue-002": {"capacity": 80, "has_dancefloor": False},
    "venue-003": {"capacity": 400, "has_dancefloor": True},
}


def run():
    r = redis.from_url(REDIS_URL)
    while True:
        try:
            r.ping()
            break
        except redis.ConnectionError:
            logger.warning("Redis not ready, retrying...")
            time.sleep(1)

    aggregators = {vid: VenueAggregator(vid, v["capacity"]) for vid, v in VENUES.items()}
    api = ApiClient(API_SERVER_URL)
    pubsub = r.pubsub()
    pubsub.psubscribe("cv.raw.*")
    logger.info("Signal service listening on cv.raw.*")

    last_flush = {vid: 0 for vid in VENUES}

    for message in pubsub.listen():
        if message["type"] not in ("message", "pmessage"):
            continue
        channel = message["channel"].decode()
        try:
            payload = json.loads(message["data"])
        except json.JSONDecodeError:
            continue

        # channel format: cv.raw.{venue_id}.{processor_name}
        parts = channel.split(".")
        if len(parts) != 4:
            continue
        _, _, venue_id, processor_name = parts
        if venue_id not in aggregators:
            continue

        agg = aggregators[venue_id]
        agg.ingest(processor_name, payload)

        # Flush cadences: occupancy 60s, demographics 5m, dancefloor 30s, vibe 5m
        now = time.time()
        cadence = {
            "occupancy": 60,
            "demographics": 300,
            "dancefloor": 30,
            "person_detector": 5,
            "heatmap": 10,
        }.get(processor_name, 60)

        if now - last_flush.get(venue_id, 0) >= cadence:
            signals = {
                "venue_id": venue_id,
                "timestamp": now,
                "occupancy": agg.compute_occupancy(),
                "demographics": agg.compute_demographics(),
                "dancefloor": agg.compute_dancefloor() if VENUES[venue_id]["has_dancefloor"] else None,
            }
            # Run vibe engine every 5m or on dancefloor updates
            if processor_name in ("demographics", "dancefloor") or now - last_flush.get(venue_id, 0) >= 300:
                engine = VibeEngine()
                hour = datetime.now().hour
                signals["vibe_zones"] = engine.evaluate(
                    signals["occupancy"], signals["demographics"], signals["dancefloor"], hour
                )

            api.post_signals(venue_id, signals)
            last_flush[venue_id] = now
            logger.info(f"Flushed signals for {venue_id}")


if __name__ == "__main__":
    run()

# """CV Pipeline entrypoint: discovers venues and spins up a worker per venue."""
# import os
# import time
# import logging
# import redis
# from processors import (
#     Anonymizer, OccupancyProcessor, DemographicsProcessor,
#     DanceFloorProcessor, PersonDetector, HeatmapProcessor,
# )
# from worker import VenueWorker
# from inference_runtime import warmup

# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# logger = logging.getLogger(__name__)

# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# MEDIAMTX_URL = os.getenv("MEDIAMTX_URL", "http://localhost:8888")
# DUMMY_MODE = os.getenv("DUMMY_MODE", "true").lower() == "true"

# VENUES = [
#     {"id": "venue-001", "capacity": 120, "has_dancefloor": True},
#     {"id": "venue-002", "capacity": 80, "has_dancefloor": False},
#     {"id": "venue-003", "capacity": 400, "has_dancefloor": True},
# ]


# def build_processors(venue: dict):
#     procs = [
#         Anonymizer(),
#         PersonDetector(),
#         OccupancyProcessor(),
#         DemographicsProcessor(),
#         HeatmapProcessor(),
#     ]
#     if venue.get("has_dancefloor"):
#         procs.append(DanceFloorProcessor())
#     return procs


# def main():
#     warmup()
#     r = redis.from_url(REDIS_URL)
#     while True:
#         try:
#             r.ping()
#             break
#         except redis.ConnectionError:
#             logger.warning("Redis not ready, retrying...")
#             time.sleep(1)

#     workers = []
#     for v in VENUES:
#         stream = f"rtsp://localhost:8554/{v['id']}"
#         procs = build_processors(v)
#         w = VenueWorker(v["id"], stream, procs, r)
#         workers.append(w)

#     logger.info(f"Starting {len(workers)} venue workers")
#     for w in workers:
#         try:
#             w.run()
#         except KeyboardInterrupt:
#             raise
#         except Exception:
#             logger.exception(f"Worker {w.venue_id} crashed, restarting in 5s")
#             time.sleep(5)


# if __name__ == "__main__":
#     main()

"""CV Pipeline entrypoint."""

import os
import time
import logging
import threading

import redis

from processors import (
    Anonymizer,
    OccupancyProcessor,
    DemographicsProcessor,
    DanceFloorProcessor,
    PersonDetector,
    HeatmapProcessor,
)

from worker import VenueWorker

from inference_runtime import warmup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# IMPORTANT:
# inside docker use service name
MEDIAMTX_RTSP = os.getenv(
    "MEDIAMTX_RTSP",
    "rtsp://vc_mediamtx:8554"
)

DUMMY_MODE = False

VENUES = [
    {
        "id": "venue-001",
        "capacity": 120,
        "has_dancefloor": True,
    },

    {
        "id": "venue-002",
        "capacity": 80,
        "has_dancefloor": False,
    },

    {
        "id": "venue-003",
        "capacity": 400,
        "has_dancefloor": True,
    },
]


def build_processors(venue: dict):

    processors = [

        Anonymizer(),

        PersonDetector(),

        OccupancyProcessor(),

        DemographicsProcessor(),

        HeatmapProcessor(),
    ]

    if venue.get("has_dancefloor"):

        processors.append(
            DanceFloorProcessor()
        )

    return processors


def run_worker(worker):

    while True:

        try:

            logger.info(
                f"[{worker.venue_id}] starting worker"
            )

            worker.run()

        except KeyboardInterrupt:

            raise

        except Exception:

            logger.exception(
                f"[{worker.venue_id}] crashed, restarting in 5s"
            )

            time.sleep(5)


def wait_for_redis():

    r = redis.from_url(REDIS_URL)

    while True:

        try:

            r.ping()

            logger.info(
                "[CV] Redis connected"
            )

            return r

        except redis.ConnectionError:

            logger.warning(
                "[CV] Redis not ready, retrying..."
            )

            time.sleep(1)


def main():

    logger.info(
        "[CV] Starting inference runtime warmup..."
    )

    warmup()

    logger.info(
        "[CV] Warmup complete"
    )

    r = wait_for_redis()

    workers = []

    for venue in VENUES:

        stream_url = (
            f"{MEDIAMTX_RTSP}/{venue['id']}"
        )

        logger.info(
            f"[{venue['id']}] stream={stream_url}"
        )

        processors = build_processors(
            venue
        )

        worker = VenueWorker(
            venue_id=venue["id"],
            stream_url=stream_url,
            processors=processors,
            redis_client=r,
        )

        workers.append(worker)

    logger.info(
        f"[CV] Starting {len(workers)} workers"
    )

    threads = []

    for worker in workers:

        t = threading.Thread(
            target=run_worker,
            args=(worker,),
            daemon=True,
        )

        t.start()

        threads.append(t)

    while True:

        time.sleep(1)


if __name__ == "__main__":

    main()
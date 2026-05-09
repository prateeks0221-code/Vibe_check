"""FastAPI server: serves venue metadata, live signals, and WebSocket stream."""
import os
import json
import asyncio
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis.asyncio as aioredis
import redis as sync_redis

from models import Venue, VenueSignals
from db import init_db, SessionLocal, VenueORM

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r_sync = sync_redis.from_url(REDIS_URL)
_signal_cache: Dict[str, VenueSignals] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="VibeCheck API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import pathlib
static_dir = pathlib.Path(__file__).parent.parent.parent / "web-player"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/")
def root():
    return {"message": "VibeCheck API v2. Visit /app/ for dashboard, /docs for API."}


@app.get("/venues", response_model=List[Venue])
def list_venues():
    db = SessionLocal()
    rows = db.query(VenueORM).all()
    db.close()
    return [Venue(
        id=r.id, name=r.name, type=r.type, capacity=r.capacity,
        has_dancefloor=r.has_dancefloor, stream_path=r.stream_path,
        lat=r.lat, lon=r.lon,
    ) for r in rows]


@app.get("/venues/{venue_id}", response_model=Venue)
def get_venue(venue_id: str):
    db = SessionLocal()
    row = db.query(VenueORM).filter(VenueORM.id == venue_id).first()
    db.close()
    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")
    return Venue(
        id=row.id, name=row.name, type=row.type, capacity=row.capacity,
        has_dancefloor=row.has_dancefloor, stream_path=row.stream_path,
        lat=row.lat, lon=row.lon,
    )


@app.get("/venues/{venue_id}/signals", response_model=VenueSignals)
def get_signals(venue_id: str):
    sig = _signal_cache.get(venue_id)
    if not sig:
        return VenueSignals(venue_id=venue_id, timestamp=0)
    return sig


@app.post("/venues/{venue_id}/signals")
def post_signals(venue_id: str, payload: VenueSignals):
    _signal_cache[venue_id] = payload
    r_sync.setex(f"signals:{venue_id}", 60, payload.model_dump_json())
    return {"ok": True}


@app.get("/venues/{venue_id}/stream")
def stream_url(venue_id: str):
    return {"hls_url": f"http://localhost:8081/{venue_id}/index.m3u8"}


@app.websocket("/ws/{venue_id}")
async def websocket_endpoint(websocket: WebSocket, venue_id: str):
    await websocket.accept()
    r_async = aioredis.from_url(REDIS_URL)
    pubsub = r_async.pubsub()
    await pubsub.psubscribe(f"cv.raw.{venue_id}.*")

    try:
        while True:
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.05)
            if msg and msg["type"] in ("message", "pmessage"):
                channel = msg["channel"]
                if isinstance(channel, bytes):
                    channel = channel.decode()
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                parts = channel.split(".")
                processor = parts[3] if len(parts) == 4 else "unknown"
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    continue
                await websocket.send_json({
                    "type": processor,
                    "venue_id": venue_id,
                    "data": payload,
                })
            else:
                await asyncio.sleep(0.02)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe()
        await r_async.aclose()

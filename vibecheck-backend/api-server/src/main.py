"""FastAPI server: serves venue metadata and live signals."""
import os
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import redis

from models import Venue, VenueSignals
from db import init_db, SessionLocal, VenueORM

app = FastAPI(title="VibeCheck API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

# In-memory signal cache (last known good)
_signal_cache: Dict[str, VenueSignals] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, venue_id: str):
        await websocket.accept()
        if venue_id not in self.active_connections:
            self.active_connections[venue_id] = []
        self.active_connections[venue_id].append(websocket)

    def disconnect(self, websocket: WebSocket, venue_id: str):
        if venue_id in self.active_connections:
            if websocket in self.active_connections[venue_id]:
                self.active_connections[venue_id].remove(websocket)

    async def broadcast_to_venue(self, venue_id: str, message: str):
        if venue_id in self.active_connections:
            # Create a list to avoid modifying during iteration if a client drops
            dead_connections = []
            for connection in self.active_connections[venue_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            for dead in dead_connections:
                self.disconnect(dead, venue_id)

manager = ConnectionManager()

# Serve static web player files
import pathlib
static_dir = pathlib.Path(__file__).parent.parent.parent / "web-player"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="static")

@app.get("/")
def root():
    return {"message": "VibeCheck API is running. Visit /app/ for the demo, or /docs for API docs."}


@app.on_event("startup")
def startup():
    init_db()


@app.get("/venues", response_model=List[Venue])
def list_venues():
    db = SessionLocal()
    rows = db.query(VenueORM).all()
    db.close()
    return [Venue(
        id=r.id,
        name=r.name,
        type=r.type,
        capacity=r.capacity,
        has_dancefloor=r.has_dancefloor,
        stream_path=r.stream_path,
        lat=r.lat,
        lon=r.lon,
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
        # Return a placeholder so the frontend never breaks
        return VenueSignals(
            venue_id=venue_id,
            timestamp=0,
            occupancy=None,
            demographics=None,
            dancefloor=None,
            vibe_zones=None,
        )
    return sig


@app.post("/venues/{venue_id}/signals")
async def post_signals(venue_id: str, payload: VenueSignals):
    """Called by signal-service to push latest aggregated state."""
    _signal_cache[venue_id] = payload
    payload_json = payload.model_dump_json()
    # Also publish to Redis for any WebSocket consumers
    r.setex(f"signals:{venue_id}", 60, payload_json)
    
    # Broadcast to connected WS clients
    await manager.broadcast_to_venue(venue_id, payload_json)
    return {"ok": True}

@app.websocket("/venues/{venue_id}/signals/ws")
async def websocket_endpoint(websocket: WebSocket, venue_id: str):
    await manager.connect(websocket, venue_id)
    try:
        # Send initial state if available
        sig = _signal_cache.get(venue_id)
        if sig:
            await websocket.send_text(sig.model_dump_json())
        
        while True:
            # Keep connection alive, wait for client messages (if any)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, venue_id)


@app.get("/venues/{venue_id}/stream")
def stream_url(venue_id: str):
    """Returns the HLS URL for The Mirror."""
    # HLS is served by a dedicated Python HTTP server on port 8081
    return {"hls_url": f"http://localhost:8081/{venue_id}/index.m3u8"}

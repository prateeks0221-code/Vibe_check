#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Use local Python venv
export PATH="$SCRIPT_DIR/.venv/bin:$PATH"

# Environment
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="sqlite:///./vibecheck.db"
export MEDIAMTX_URL="http://localhost:8888"
export API_SERVER_URL="http://localhost:8000"
export DUMMY_MODE="true"

# Python path so imports work across modules
export PYTHONPATH="$SCRIPT_DIR/api-server/src:$SCRIPT_DIR/cv-pipeline/src:$SCRIPT_DIR/signal-service/src"

# Create logs dir
mkdir -p logs hls/venue-001 hls/venue-002 hls/venue-003

echo "========================================"
echo "  VibeCheck Demo Launcher"
echo "========================================"
echo ""

# 1. Redis
echo "[1/5] Starting Redis..."
if ! redis-cli ping >/dev/null 2>&1; then
    redis-server --daemonize yes --logfile "$SCRIPT_DIR/logs/redis.log"
    sleep 1
fi
redis-cli ping >/dev/null 2>&1 && echo "       Redis OK" || { echo "       Redis failed"; exit 1; }

# 2. MediaMTX (RTSP ingest router)
echo "[2/5] Starting MediaMTX..."
if [ -f "$SCRIPT_DIR/mediamtx/mediamtx" ]; then
    nohup "$SCRIPT_DIR/mediamtx/mediamtx" "$SCRIPT_DIR/mediamtx/mediamtx.yml" > "$SCRIPT_DIR/logs/mediamtx.log" 2>&1 &
    sleep 3
    echo "       MediaMTX OK (RTSP on :8554, HLS on :8888)"
else
    echo "       MediaMTX binary not found!"
    exit 1
fi

# 3. HLS transcoding servers — pull RTSP from MediaMTX and serve as HLS
#    -c:v copy  = pass video through without re-encoding (fast, low latency)
#    -an        = drop audio (not needed for The Mirror, avoids PCM issues)
echo "[3/5] Starting HLS transcoding servers..."

for VID in venue-001 venue-002 venue-003; do
    rm -f "$SCRIPT_DIR/hls/$VID"/*.ts "$SCRIPT_DIR/hls/$VID"/*.m3u8
    nohup /opt/homebrew/bin/ffmpeg \
        -rtsp_transport tcp \
        -fflags +discardcorrupt \
        -i "rtsp://localhost:8554/$VID" \
        -c:v copy -an \
        -f hls -hls_time 2 -hls_list_size 15 \
        -hls_flags delete_segments+append_list \
        "$SCRIPT_DIR/hls/$VID/index.m3u8" \
        > "$SCRIPT_DIR/logs/hls-$VID.log" 2>&1 &
    echo "       HLS generator for $VID started"
done

# Custom HLS HTTP server with CORS + no-cache
nohup python "$SCRIPT_DIR/hls_server.py" 8081 "$SCRIPT_DIR/hls" > "$SCRIPT_DIR/logs/hls-server.log" 2>&1 &
echo "       HLS HTTP server OK (http://localhost:8081)"

# 4. API Server (FastAPI + static web player)
echo "[4/5] Starting API Server..."
nohup uvicorn api-server.src.main:app --host 0.0.0.0 --port 8000 > "$SCRIPT_DIR/logs/api-server.log" 2>&1 &
sleep 2
curl -s http://localhost:8000/ >/dev/null && echo "       API Server OK (http://localhost:8000)" || echo "       API Server starting..."

# 5. Signal Service
echo "[5/5] Starting Signal Service..."
nohup python signal-service/src/main.py > "$SCRIPT_DIR/logs/signal-service.log" 2>&1 &
sleep 1
echo "       Signal Service started"

# 6. CV Pipeline
echo "[6/6] Starting CV Pipeline..."
nohup python cv-pipeline/src/main.py > "$SCRIPT_DIR/logs/cv-pipeline.log" 2>&1 &
sleep 1
echo "       CV Pipeline started"

echo ""
echo "========================================"
echo "  All services launched!"
echo "========================================"
echo ""
echo "  Local web app:  http://localhost:8000/app/"
echo "  API docs:       http://localhost:8000/docs"
echo "  HLS endpoint:   http://localhost:8081"
echo "  MediaMTX HLS:   http://localhost:8888"
echo ""
echo "  LAN web app:    http://$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -1):8000/app/"
echo ""
echo "  To expose publicly (for mobile):"
echo "    ngrok http 8000"
echo "    ngrok http 8081"
echo ""
echo "  Then open the API ngrok URL + /app/?hls=<HLS-ngrok-host>"
echo ""
echo "  Logs: ./logs/"
echo "  Stop: ./stop-demo.sh"
echo ""
echo "========================================"

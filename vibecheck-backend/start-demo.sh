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
mkdir -p logs

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

# 2. MediaMTX (RTSP router) + HLS generation via ffmpeg
echo "[2/5] Starting MediaMTX + HLS generators..."
if [ -f "$SCRIPT_DIR/mediamtx/mediamtx" ]; then
    nohup "$SCRIPT_DIR/mediamtx/mediamtx" "$SCRIPT_DIR/mediamtx/mediamtx.yml" > "$SCRIPT_DIR/logs/mediamtx.log" 2>&1 &
    sleep 2
    echo "       MediaMTX OK (RTSP on port 8554)"
else
    echo "       MediaMTX binary not found!"
    exit 1
fi

# Start ffmpeg HLS generators for each venue
mkdir -p "$SCRIPT_DIR/hls/venue-001" "$SCRIPT_DIR/hls/venue-002" "$SCRIPT_DIR/hls/venue-003"
nohup /opt/homebrew/bin/ffmpeg -f lavfi -i testsrc=size=1280x720:rate=15 -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -f hls -hls_time 2 -hls_list_size 5 -hls_flags delete_segments "$SCRIPT_DIR/hls/venue-001/index.m3u8" > "$SCRIPT_DIR/logs/hls-venue-001.log" 2>&1 &
nohup /opt/homebrew/bin/ffmpeg -f lavfi -i testsrc=size=1280x720:rate=15 -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -f hls -hls_time 2 -hls_list_size 5 -hls_flags delete_segments "$SCRIPT_DIR/hls/venue-002/index.m3u8" > "$SCRIPT_DIR/logs/hls-venue-002.log" 2>&1 &
nohup /opt/homebrew/bin/ffmpeg -f lavfi -i testsrc=size=1280x720:rate=15 -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -f hls -hls_time 2 -hls_list_size 5 -hls_flags delete_segments "$SCRIPT_DIR/hls/venue-003/index.m3u8" > "$SCRIPT_DIR/logs/hls-venue-003.log" 2>&1 &

# Serve HLS files on port 8081 (8888/8889 used by MediaMTX)
nohup python3 -m http.server 8081 --directory "$SCRIPT_DIR/hls" > "$SCRIPT_DIR/logs/hls-server.log" 2>&1 &
echo "       HLS server OK (http://localhost:8081)"

# 3. API Server (FastAPI + static web player)
echo "[3/5] Starting API Server..."
nohup uvicorn api-server.src.main:app --host 0.0.0.0 --port 8000 --reload > "$SCRIPT_DIR/logs/api-server.log" 2>&1 &
sleep 2
curl -s http://localhost:8000/venues >/dev/null && echo "       API Server OK (http://localhost:8000)" || echo "       API Server starting..."

# 4. Signal Service
echo "[4/5] Starting Signal Service..."
nohup python signal-service/src/main.py > "$SCRIPT_DIR/logs/signal-service.log" 2>&1 &
sleep 1
echo "       Signal Service started"

# 5. CV Pipeline
echo "[5/5] Starting CV Pipeline..."
nohup python cv-pipeline/src/main.py > "$SCRIPT_DIR/logs/cv-pipeline.log" 2>&1 &
sleep 1
echo "       CV Pipeline started"

echo ""
echo "========================================"
echo "  All services launched!"
echo "========================================"
echo ""
echo "  Local:     http://localhost:8000"
echo "  LAN:       http://$(ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -1):8000"
echo "  API docs:  http://localhost:8000/docs"
echo "  HLS:       http://localhost:8081"
echo ""
echo "  To expose publicly (for mobile):"
echo "    ngrok http 8000"
echo "    ngrok http 8081  (in another terminal for HLS)"
echo ""
echo "  Then open the 8000 ngrok URL on your phone."
echo ""
echo "  Logs: ./logs/"
echo "  Stop: ./stop-demo.sh"
echo ""
echo "========================================"

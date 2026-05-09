#!/usr/bin/env bash
echo "Stopping VibeCheck demo services..."

# Kill MediaMTX
pkill -f "mediamtx.*mediamtx.yml" 2>/dev/null || true

# Kill ffmpeg HLS generators (RTSP pullers)
pkill -f "ffmpeg.*rtsp://localhost:8554" 2>/dev/null || true
pkill -f "ffmpeg.*hls/venue" 2>/dev/null || true
pkill -f "ffmpeg.*testsrc" 2>/dev/null || true

# Kill Python processes
pkill -f "uvicorn api-server.src.main:app" 2>/dev/null || true
pkill -f "python signal-service/src/main.py" 2>/dev/null || true
pkill -f "python cv-pipeline/src/main.py" 2>/dev/null || true
pkill -f "python hls_server.py" 2>/dev/null || true
pkill -f "python3 -m http.server" 2>/dev/null || true

# Kill ngrok tunnels
pkill -f "ngrok http" 2>/dev/null || true

# Kill Redis (if we started it)
pkill -f "redis-server.*logs/redis.log" 2>/dev/null || true

echo "All services stopped."

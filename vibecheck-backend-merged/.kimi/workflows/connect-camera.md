# Workflow: Connect a Real CCTV Camera

## Goal
Replace a dummy test pattern with a real camera feed.

## Steps

### 1. Get the camera RTSP URL

Common formats:
```
rtsp://admin:password@192.168.1.100:554/stream1
rtsp://192.168.1.100:554/user=admin&password=&channel=1&stream=0.sdp
rtsp://192.168.0.108:8080/h264_pcm.sdp
```

Test it locally:
```bash
ffprobe -rtsp_transport tcp -i rtsp://your-camera-url
```

### 2. Edit MediaMTX config

Edit `mediamtx/mediamtx.yml`:

```yaml
venue-001:
  source: rtsp://your-camera-url
  # Comment out or remove runOnInit when using a real camera
  # runOnInit: ...
  # runOnInitRestart: yes
```

### 3. Restart

```bash
./stop-demo.sh && ./start-demo.sh
```

### 4. Verify MediaMTX is receiving

```bash
tail -f logs/mediamtx.log | grep venue-001
```

You should see:
```
[path venue-001] stream is available and online, 1 track (H264)
```

### 5. Verify HLS is generating

```bash
ls hls/venue-001/
# Should show index.m3u8 and index*.ts files
```

### 6. Test in browser

Open http://localhost:8000/app/ and select the venue. The video should show your camera feed.

## Troubleshooting

### "received RTP packet with unknown payload type"

Your camera sends incompatible audio. The HLS generator already drops audio (`-an`), but MediaMTX may still complain. This is usually harmless.

### "Cannot open input" from ffmpeg

- Check the RTSP URL with `ffprobe` first.
- Try adding `-rtsp_transport tcp` to the ffmpeg HLS generator (already default).
- Check firewall rules on the camera.

### Video is black/blank

- The camera may require authentication. Include credentials in the URL: `rtsp://user:pass@ip/stream`.
- The camera may use a different codec (H265). The HLS generator only supports H264 passthrough. Transcode if needed.

### High latency (>10 seconds)

- The camera may buffer heavily. Reduce buffer in the camera settings.
- Use `-fflags nobuffer -flags low_delay` in ffmpeg if needed.
- Consider using MediaMTX's native WebRTC output (`:8889`) for lower latency.

## Reverting to Dummy

```yaml
venue-001:
  source: publisher
  runOnInit: /opt/homebrew/bin/ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=15 -pix_fmt yuv420p -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://localhost:8554/venue-001
  runOnInitRestart: yes
```

```bash
./stop-demo.sh && ./start-demo.sh
```

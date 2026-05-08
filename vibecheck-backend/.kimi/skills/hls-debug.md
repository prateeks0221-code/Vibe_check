# Skill: Debug HLS Streams

## Checklist

### 1. Is the HLS playlist valid?

```bash
curl -s http://localhost:8081/venue-001/index.m3u8
```

Expected:
```
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:2
#EXT-X-MEDIA-SEQUENCE:123
#EXTINF:2.000000,
index123.ts
```

### 2. Are segments being generated?

```bash
ls -la hls/venue-001/
```

Should show `.ts` files with recent timestamps.

### 3. Is the segment downloadable?

```bash
SEG=$(curl -s http://localhost:8081/venue-001/index.m3u8 | grep ".ts" | tail -1 | tr -d '\r')
curl -sI "http://localhost:8081/venue-001/$SEG" | head -1
# Should return HTTP/1.0 200 OK
```

### 4. Is ffmpeg running?

```bash
ps aux | grep "ffmpeg.*venue-001"
```

### 5. Is MediaMTX serving the RTSP stream?

```bash
curl -sI http://localhost:8888/venue-001/index.m3u8
# May return 404 if hlsAlwaysRemux is false — that's OK, we use our own HLS server
```

### 6. Test with ffplay

```bash
ffplay http://localhost:8081/venue-001/index.m3u8
```

### 7. Test with VLC

Open VLC → Media → Open Network Stream → `http://localhost:8081/venue-001/index.m3u8`

### 8. Check browser console

Open the web player, open DevTools → Console. Look for:
- `hls.js` errors
- Mixed content warnings (HTTP vs HTTPS)
- CORS errors

## Common Fixes

| Issue | Fix |
|-------|-----|
| Playlist empty | Wait 5s for first segment. Check ffmpeg is running. |
| 404 on segments | Segment deleted before browser downloaded. Increase `hls_list_size`. |
| Video stutters | Camera frame rate inconsistent. Use `-r 15` to force output fps. |
| High latency | Camera buffers heavily. Use `-fflags nobuffer`. |
| No video in Safari | Add `muted playsinline` to `<video>`. Use HLS not DASH. |
| CORS error | HLS server missing `Access-Control-Allow-Origin: *`. Check `hls_server.py`. |

# Workflow: Test on a Mobile Device

## Prerequisites
- ngrok installed and authenticated (`ngrok config add-authtoken <token>`)
- `./start-demo.sh` is running locally

## Steps

### 1. Start ngrok tunnels

Open **two separate terminals**:

```bash
# Terminal 1 — API + web player
ngrok http 8000
```

```bash
# Terminal 2 — HLS video streams
ngrok http 8081
```

### 2. Get the URLs

Terminal 1 shows something like:
```
Forwarding https://a1b2-12-34-56-78.ngrok-free.app -> http://localhost:8000
```

Terminal 2 shows something like:
```
Forwarding https://c3d4-12-34-56-78.ngrok-free.app -> http://localhost:8081
```

### 3. Open on phone

Construct the URL:

```
https://a1b2-12-34-56-78.ngrok-free.app/app/?hls=c3d4-12-34-56-78.ngrok-free.app
```

Open this in **Safari (iOS)** or **Chrome (Android)**.

### 4. What to check

- [ ] Page loads (not blank)
- [ ] Venue selector shows venue names
- [ ] Video plays (red LIVE badge visible)
- [ ] Occupancy card updates within 60s
- [ ] Demographics card appears within 5m
- [ ] Dance floor card updates within 30s (clubs only)
- [ ] Vibe zones pills appear
- [ ] Can switch between venues

### 5. Common mobile issues

**Blank page:**
- Check that `/app/` has the trailing slash. Without it, FastAPI may 404.
- Open `https://<api-ngrok>/app/?hls=<hls-ngrok>` not `/app?hls=...`

**Video shows "loading" forever:**
- Check `https://<hls-ngrok>/venue-001/index.m3u8` in a browser. Should show `#EXTM3U`.
- Check browser console for mixed-content errors (HTTP vs HTTPS).
- Safari requires `muted playsinline` attributes (already present).

**Video plays but no signals:**
- Wait 60 seconds for first occupancy flush.
- Open `https://<api-ngrok>/venues/venue-001/signals` directly.

**ngrok "Visit Site" warning:**
- Free ngrok shows an interstitial on first visit. Tap "Visit Site".
- Or sign up for ngrok Pro to remove it.

### 6. Local network alternative (no ngrok)

If phone and laptop are on the same WiFi:

```
http://<laptop-ip>:8000/app/
```

Find laptop IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### 7. Stop ngrok

```bash
pkill -f "ngrok http"
```

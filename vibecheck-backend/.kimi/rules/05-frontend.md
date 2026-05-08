# Rule 05: Web Player (Frontend)

## Stack

- **hls.js** for HLS playback
- **Vanilla HTML/JS** — no React, Vue, or build tools
- **CSS in `<style>`** inside `index.html` — no external CSS files
- **Mobile-first** design: max-width 480px container, touch-friendly controls

## File

Everything lives in `web-player/index.html`. One file. That's it.

## Dynamic URLs

The player auto-detects its environment:

```javascript
const urlParams = new URLSearchParams(window.location.search);
const HLS_HOST = urlParams.get('hls') || `${window.location.hostname}:8081`;
const API_BASE = '';  // API served from same origin
```

When behind ngrok, append `?hls=<HLS-ngrok-host>` to the URL.

## Video Player Setup

```javascript
const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
const streamUrl = `${protocol}//${HLS_HOST}/${venueId}/index.m3u8`;

if (Hls.isSupported()) {
    hls = new Hls({ liveSyncDurationCount: 2, liveMaxLatencyDurationCount: 5 });
    hls.loadSource(streamUrl);
    hls.attachMedia(video);
    hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
} else if (video.canPlayType('application/vnd.apple.mpegurl')) {
    video.src = streamUrl;
    video.addEventListener('loadedmetadata', () => video.play());
}
```

## Signal Polling

Poll every 5 seconds:

```javascript
setInterval(() => {
    const sel = document.getElementById('venueSelect');
    if (sel) pollSignals(sel.value);
}, 5000);
```

## Adding a New Signal Card

In `renderSignals()`, add a new block:

```javascript
// Bar Queue
if (data.bar_queue) {
    const bq = data.bar_queue;
    html += `
        <div class="card">
            <h2>Bar Queue</h2>
            <div class="occupancy">
                <span class="pct">${bq.queue_count}</span>
                <span class="label">people waiting</span>
            </div>
        </div>
    `;
}
```

## Styling

- Use CSS custom properties sparingly. Hardcode colors for now.
- Cards: `background: #161616; border-radius: 12px; padding: 16px;`
- Pills: `background: #2a2a2a; padding: 6px 12px; border-radius: 20px;`
- Occupancy colors: green (`#4caf50`) ≤30%, amber (`#ff9800`) ≤60%, red (`#f44336`) >60%

## Testing

- Test on actual mobile Safari and Chrome. Desktop browser dev tools are not enough.
- Check that video autoplays with `muted` and `playsinline` attributes.
- Verify HLS works over HTTPS (ngrok) — mixed content will block playback.

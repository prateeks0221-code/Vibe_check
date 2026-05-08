# VibeCheck — Product & Design Doctrine

**For:** Product Owner, Design Lead, Frontend Engineers, Brand Stakeholders  
**Version:** MVP v1.0  
**Status:** Living document

---

## 1. Product Thesis

VibeCheck is not a utility. It is a **truth layer** for nightlife.

Every other product in this space gives you static information — a Yelp review from Tuesday, an Instagram post from last month, a Google rating that hasn't changed in a year. VibeCheck gives you the **now**. It answers the only question that matters at 11:47 PM on a Saturday: *"Is this place actually good right now?"*

This truth-telling function is our entire brand. Every design decision, every interaction, every word of copy must reinforce the feeling that what you are seeing is real, unfiltered, and current.

---

## 2. Design Principles

### P1: Brutal Honesty

The UI must feel like a direct feed from reality. No smoothing, no averaging, no hiding bad news. If a venue is dead, it says "Dead". If it's packed, it says "Packed" in red. The user should trust the platform precisely because it does not flatter.

### P2: Speed Over Depth

A user deciding where to go is time-pressured and socially anxious. Every screen must deliver its signal in under 2 seconds of attention. No onboarding. No tutorials. No "learn more" links. The information hierarchy is: **video → occupancy → crowd → vibe → details**.

### P3: Mobile-First, Thumb-Optimized

This product is used while walking, in Ubers, in groups. All interactions must be one-thumbable. The primary action (switch venue) is a dropdown at the top. The secondary action (scroll for signals) is vertical. No horizontal swiping. No tiny tap targets.

### P4: Dark Mode by Default

Nightlife happens at night. The app is dark by default not as an option but as a statement. The background is `#0a0a0a` — not pure black, which feels sterile, but a very dark charcoal that absorbs light the way a club interior does.

### P5: Signal Over Chrome

Every visual element must earn its place. The video is the hero. Signal cards are secondary. Decorative elements are forbidden. The only "branded" element is the small VibeCheck wordmark at the top.

---

## 3. Visual System

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `bg-primary` | `#0a0a0a` | App background |
| `bg-card` | `#161616` | Signal cards |
| `bg-elevated` | `#1e1e1e` | Hover states, dropdowns |
| `text-primary` | `#ffffff` | Headings, numbers |
| `text-secondary` | `#888888` | Labels, timestamps |
| `text-muted` | `#666666` | Disclaimers, placeholders |
| `accent-green` | `#4caf50` | Quiet occupancy (0–30%) |
| `accent-amber` | `#ff9800` | Busy occupancy (31–60%) |
| `accent-red` | `#f44336` | Packed occupancy (61–100%) |
| `accent-vibe` | `#ff6b6b` | Vibe zone pills |
| `accent-gradient` | `linear-gradient(90deg, #ff6b6b, #feca57)` | Energy bars |

### Typography

- **Primary:** System font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`)
- **Rationale:** No custom fonts to load. The product must feel native to the OS it runs on. Speed over personality.
- **Scale:**
  - Venue name (dropdown): `1rem` / 16px
  - Occupancy percentage: `2.5rem` / 40px, weight 700
  - Signal labels: `0.875rem` / 14px, uppercase, letter-spacing `0.04em`
  - Body/disclaimer: `0.875rem` / 14px
  - Timestamp: `0.75rem` / 12px

### Spacing

- Container max-width: `480px` (phone-first)
- Page padding: `16px`
- Card padding: `16px`
- Card border-radius: `12px`
- Card gap: `12px`
- Pill border-radius: `20px`
- Pill padding: `6px 12px`

### Motion

- **Energy bar transitions:** `width 0.5s ease`
- **Live dot pulse:** `1.2s infinite` CSS keyframe
- **Card entrance:** none. Cards appear instantly. This is a live product, not a marketing page.
- **Video buffer:** show a subtle `#111` background behind the video element. No spinners. Spinners feel like failure.

---

## 4. Component Specs

### The Mirror (Video Player)

- Full-width, aspect-ratio `16/9`, border-radius `12px`
- Red LIVE badge: absolute positioned, top-left, `4px 10px` padding, `20px` border-radius, white text, pulsing dot
- Controls: `muted`, `playsinline`, `autoplay`
- No scrubber. No pause button. This is live video, not a recording.
- Background color behind video: `#111` (prevents flash of white during load)

### Occupancy Card

- Large percentage number in color-coded weight 700
- Pill label next to it (Quiet / Getting There / Busy / Packed)
- Subtext: `"{head_count} / {capacity} people"` in muted
- Color logic: ≤30% green, ≤60% amber, >60% red

### Demographics Card

- Two pill tags: primary age bracket, gender split
- Horizontal bar showing male/female proportion
- Disclaimer text: `"Estimates based on visual analysis. Approximate only."`
- If no data yet: show `"Crowd data coming soon…"` placeholder

### Dance Floor Card

- Large state text (Dead / Warming Up / Active / Raging)
- Energy bar 0–100 with gradient fill
- Subtext: `"Energy {score}/100"`
- Hidden entirely for cafes (not shown as zero)

### Vibe Zones Card

- 1–3 pill tags in row
- Background: `accent-vibe` at 13% opacity, text `accent-vibe`
- If no descriptors match: show `"Vibe data coming soon…"` placeholder
- If venue has no descriptor bank: show `"Vibe data coming soon…"` placeholder

### Venue Selector

- Full-width dropdown, `#111` background, `1px solid #333` border
- Venue name + type in parentheses
- Switching venue destroys and recreates the HLS player instance

---

## 5. User Journeys

### Journey A: The Decider (Primary)

**User:** 24-year-old, group chat open, 10:30 PM, deciding where to go.

**Flow:**
1. Opens VibeCheck (bookmark or home screen)
2. Sees default venue (last viewed or nearest)
3. Taps dropdown, scans list, picks venue
4. Watches The Mirror for 3–5 seconds
5. Glances at occupancy + crowd
6. Checks vibe zones
7. Screenshots or shares link in group chat
8. Closes app. Decision made.

**Design implications:**
- First paint must be <1s
- Video must start playing within 3s
- All signals must be visible without scrolling
- Shareability: every venue page should have a shareable URL

### Journey B: The Explorer

**User:** 22-year-old, early evening, browsing options for later.

**Flow:**
1. Opens VibeCheck
2. Swaps through 3–4 venues
3. Compares occupancy and vibe zones
4. Mentally shortlists 2 venues
5. Returns later to check again

**Design implications:**
- Venue switch must be <2s (destroy/recreate HLS)
- Signal cache prevents loading states on revisit
- Browse view (post-MVP) should show all venues at a glance

### Journey C: The Venue Operator

**User:** Bar manager, back office, checking how the night is going.

**Flow:**
1. Opens operator dashboard (post-MVP)
2. Sees live occupancy, crowd mix, dance floor energy
3. Compares to historical baseline
4. Decides whether to run a promotion or adjust staffing

**Design implications:**
- Operator dashboard is a separate view (not the consumer UI)
- Needs historical charts, not just live values
- Needs blackout toggle (private events)

---

## 6. Voice & Tone

### Consumer-Facing Copy

- **Direct.** `"73%"` not `"The venue is currently at 73% capacity."`
- **Human.** `"Packed"` not `"High occupancy threshold exceeded."`
- **Humble.** `"Approximate only"` not `"AI-powered precision analytics."`
- **Urgent.** `"LIVE"` badge, red dot, timestamp.

### Examples

| Don't | Do |
|-------|-----|
| "Real-time venue analytics platform" | "See inside before you go" |
| "Computer vision-derived occupancy estimation" | "How full is it right now?" |
| "Demographic profiling via neural network" | "Mostly 25–34 tonight" |
| "Insufficient data for this signal" | "Coming soon…" |

### Error States

- Stream offline: `"Live video unavailable. Signals may be delayed."` (not "Error 404")
- No data yet: `"{Signal} data coming soon…"` (not "Null")
- Venue closed: `"This venue is closed right now."` (not "0% occupancy")

---

## 7. Accessibility

- All text meets WCAG AA contrast against `#0a0a0a` or `#161616`
- Occupancy color is supplementary; the number itself is the primary signal
- Video has `muted` by default (respects user preference)
- All interactive elements have minimum 44px tap target
- Respect `prefers-reduced-motion` (disable pulse animation)

---

## 8. Roadmap

### MVP (v1.0) — Now
- [x] The Mirror (live stream)
- [x] Occupancy percentage
- [x] Age bracket & gender split
- [x] Dance floor activity
- [x] Vibe Zones (operator-curated)
- [x] 3 demo venues
- [x] Mobile web player

### v1.1 — Post-MVP (Month 2)
- [ ] Consumer browse view (grid of all venues)
- [ ] Map view (venue pins with live occupancy)
- [ ] Push notifications ("Your saved venue is heating up")
- [ ] Favorites / saved venues
- [ ] Shareable venue URLs with preview cards

### v1.2 — Scale (Month 4)
- [ ] Operator dashboard (blackout mode, descriptor editing)
- [ ] Historical data charts ("How busy was it last Friday?")
- [ ] Predictive vibe (ML-based forecast for tonight)
- [ ] Dynamic offers (venue pushes promotions during slow periods)

### v2.0 — Platform (Month 6)
- [ ] Public API for third-party integrations (Uber, Google Maps)
- [ ] Data licensing to hospitality analytics platforms
- [ ] White-label offering for venue chains
- [ ] iOS and Android native apps

---

## 9. Metrics That Matter

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time-to-decision | <30s | Session duration for users who view ≥1 venue |
| Venue switch rate | 3+ per session | Average venues viewed per session |
| Stream play rate | >60% | % of venue views where video plays >10s |
| Return rate | 40% in 7 days | % of first-time users who return |
| Signal uptime | >95% | % of operating hours with live signals |
| Descriptor adoption | 100% | % of venues with configured vibe library |

---

## 10. Brand Identity

### Name
**VibeCheck** — lowercase in body copy, Title Case in headers. Never "Vibe Check" (two words) or "Vibecheck" (one word, lowercase).

### Logo
Wordmark only. No icon. The product is the camera feed, not a logo. The wordmark uses the system font stack, weight 600, letter-spacing `-0.02em`.

### Tagline
"See inside before you go."

### Social Presence
- Instagram: Short clips of The Mirror feeds (anonymized) with venue tags
- TikTok: "POV: you're deciding where to go tonight" — split screen of empty vs packed venues
- Twitter/X: Real-time occupancy updates for major nightlife cities

---

## 11. Competitive Differentiation

| Competitor | What they do | What VibeCheck does differently |
|------------|-------------|-----------------------------------|
| Yelp | Static reviews | Live video + live data |
| Google Maps | Hours + ratings | Real-time occupancy |
| Instagram | Curated photos | Unfiltered reality |
| Resy | Reservations | No booking, just truth |
| Nightlife apps | Event listings | What's happening *right now* |

---

## 12. Design Review Checklist

Before any UI change ships:

- [ ] Does it load in under 2s on 4G?
- [ ] Can a user understand the signal in under 2s?
- [ ] Does it work with one thumb?
- [ ] Is the video visible above the fold?
- [ ] Are colors used only for supplementary information?
- [ ] Is the copy direct, human, and humble?
- [ ] Does it respect dark mode?
- [ ] Does it degrade gracefully if a signal is missing?
- [ ] Would you trust this if you were making a $100 night-out decision?

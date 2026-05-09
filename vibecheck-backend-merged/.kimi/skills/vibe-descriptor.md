# Skill: Add a Vibe Zone Descriptor

## What is a Vibe Zone?

A human-readable label (e.g., "Cocktail crowd", "Student energy") that activates when live signals match predefined conditions.

## How It Works

The `VibeEngine` evaluates current signals against a descriptor bank and returns the top 3 matches.

## Adding a New Descriptor

### 1. Edit `signal-service/src/vibe_engine.py`

Add to `DEFAULT_DESCRIPTORS`:

```python
{
    "label": "Rooftop sunset",
    "conditions": {
        "occupancy_min": 20,
        "occupancy_max": 50,
        "primary_age_bracket": "25-34",
        "hour_min": 17,
        "hour_max": 20,
    },
},
```

### 2. Available Condition Fields

| Field | Type | Description |
|-------|------|-------------|
| `occupancy_min` | int (0-100) | Minimum occupancy percentage |
| `occupancy_max` | int (0-100) | Maximum occupancy percentage |
| `primary_age_bracket` | str | "18-24", "25-34", "35-49", "50+" |
| `dancefloor_state` | str | "Dead", "Warming Up", "Active", "Raging" |
| `hour_min` | int (0-23) | Minimum hour of day |
| `hour_max` | int (0-23) | Maximum hour of day |

All conditions are AND-ed. A missing condition means "any value accepted".

### 3. Test

```bash
./stop-demo.sh && ./start-demo.sh
```

Wait for signals to populate, then:

```bash
curl http://localhost:8000/venues/venue-001/signals | python3 -m json.tool | grep vibe_zones
```

### 4. Operator-Curated Descriptors (Future)

Post-MVP, descriptors will be stored in the database and editable by venue operators via a dashboard. For now, they are hardcoded in `vibe_engine.py`.

## Confidence Scoring

Confidence is the count of matched conditions (1-4). Higher = more specific match. The engine returns top 3 by confidence.

## Example Descriptor Bank

```python
DEFAULT_DESCRIPTORS = [
    {"label": "Cocktail crowd", "conditions": {"occupancy_min": 40, "occupancy_max": 80, "primary_age_bracket": "25-34"}},
    {"label": "Student energy", "conditions": {"primary_age_bracket": "18-24", "occupancy_min": 50}},
    {"label": "Afterwork wind-down", "conditions": {"occupancy_min": 20, "occupancy_max": 60, "hour_min": 17, "hour_max": 20}},
    {"label": "Pre-drinks mode", "conditions": {"occupancy_min": 30, "occupancy_max": 70, "hour_min": 19, "hour_max": 23}},
    {"label": "Deep house set", "conditions": {"dancefloor_state": "Active", "occupancy_min": 60}},
    {"label": "Intimate session", "conditions": {"occupancy_max": 40}},
    {"label": "Weekend warmup", "conditions": {"occupancy_min": 30, "occupancy_max": 60, "dancefloor_state": "Warming Up"}},
    {"label": "Peak time", "conditions": {"occupancy_min": 80, "dancefloor_state": "Active"}},
    {"label": "Late night rage", "conditions": {"occupancy_min": 70, "dancefloor_state": "Raging", "hour_min": 0, "hour_max": 4}},
    {"label": "Quiet catch-up", "conditions": {"occupancy_max": 30}},
]
```

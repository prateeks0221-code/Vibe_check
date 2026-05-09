"""Rule engine for F5 — Vibe Zones."""
from typing import Dict, List, Optional


class VibeEngine:
    """
    Evaluates venue signal state against operator-curated descriptor banks.
    In production this loads descriptor rules from PostgreSQL.
    """

    DEFAULT_DESCRIPTORS = [
        {"label": "Cocktail crowd", "conditions": {"occupancy_min": 40, "occupancy_max": 80, "primary_age_bracket": "25-34"}},
        {"label": "Student energy", "conditions": {"primary_age_bracket": "18-24", "occupancy_min": 50}},
        {"label": "Afterwork wind-down", "conditions": {"occupancy_min": 20, "occupancy_max": 60, "primary_age_bracket": "25-34", "hour_min": 17, "hour_max": 20}},
        {"label": "Pre-drinks mode", "conditions": {"occupancy_min": 30, "occupancy_max": 70, "hour_min": 19, "hour_max": 23}},
        {"label": "Deep house set", "conditions": {"dancefloor_state": "Active", "occupancy_min": 60}},
        {"label": "Intimate session", "conditions": {"occupancy_max": 40}},
        {"label": "Weekend warmup", "conditions": {"occupancy_min": 30, "occupancy_max": 60, "dancefloor_state": "Warming Up"}},
        {"label": "Peak time", "conditions": {"occupancy_min": 80, "dancefloor_state": "Active"}},
        {"label": "Late night rage", "conditions": {"occupancy_min": 70, "dancefloor_state": "Raging", "hour_min": 0, "hour_max": 4}},
        {"label": "Quiet catch-up", "conditions": {"occupancy_max": 30}},
    ]

    def __init__(self, venue_descriptors: Optional[List[dict]] = None):
        self.descriptors = venue_descriptors or self.DEFAULT_DESCRIPTORS

    def evaluate(self, occupancy: Optional[dict], demographics: Optional[dict], dancefloor: Optional[dict], hour: int) -> List[dict]:
        matches = []
        for d in self.descriptors:
            score = self._score(d["conditions"], occupancy, demographics, dancefloor, hour)
            if score > 0:
                matches.append({"label": d["label"], "confidence": score})
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches[:3]

    def _score(self, cond, occ, demo, df, hour) -> int:
        score = 0
        # Occupancy
        occ_pct = occ.get("percentage", 0) if occ else 0
        if "occupancy_min" in cond and occ_pct < cond["occupancy_min"]:
            return 0
        if "occupancy_max" in cond and occ_pct > cond["occupancy_max"]:
            return 0
        if "occupancy_min" in cond or "occupancy_max" in cond:
            score += 1

        # Age bracket
        age = demo.get("primary_age_bracket", "") if demo else ""
        if "primary_age_bracket" in cond:
            if age != cond["primary_age_bracket"]:
                return 0
            score += 1

        # Dance floor state
        df_state = df.get("state", "") if df else ""
        if "dancefloor_state" in cond:
            if df_state != cond["dancefloor_state"]:
                return 0
            score += 1

        # Time of day
        if "hour_min" in cond and hour < cond["hour_min"]:
            return 0
        if "hour_max" in cond and hour > cond["hour_max"]:
            return 0
        if "hour_min" in cond or "hour_max" in cond:
            score += 1

        return score

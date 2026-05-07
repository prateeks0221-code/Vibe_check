"""Pydantic schemas for VibeCheck API."""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class OccupancySignal(BaseModel):
    percentage: int
    label: str
    head_count: int
    capacity: int


class DemographicsSignal(BaseModel):
    primary_age_bracket: str
    male_presenting_pct: int
    female_presenting_pct: int


class DanceFloorSignal(BaseModel):
    energy_score: int
    raw_score: int
    state: str


class VibeZone(BaseModel):
    label: str
    confidence: int


class VenueSignals(BaseModel):
    venue_id: str
    timestamp: float
    occupancy: Optional[OccupancySignal] = None
    demographics: Optional[DemographicsSignal] = None
    dancefloor: Optional[DanceFloorSignal] = None
    vibe_zones: Optional[List[VibeZone]] = None


class Venue(BaseModel):
    id: str
    name: str
    type: str  # cafe, bar, club
    capacity: int
    has_dancefloor: bool
    stream_path: str
    lat: float
    lon: float

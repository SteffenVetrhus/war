from pydantic import BaseModel
from typing import Optional


class BombingIncident(BaseModel):
    id: str
    title: str
    location: str
    latitude: float
    longitude: float
    date: str
    killed: int = 0
    wounded: int = 0
    notable_figures: list[str] = []
    description: str = ""
    source: str = ""
    source_url: str = ""
    attacker: str = ""
    origin_location: str = ""
    origin_latitude: Optional[float] = None
    origin_longitude: Optional[float] = None


class StatsResponse(BaseModel):
    total_incidents: int
    total_killed: int
    total_wounded: int
    sources_count: int
    last_updated: Optional[str] = None


class ScrapeResponse(BaseModel):
    status: str
    new_incidents: int
    message: str

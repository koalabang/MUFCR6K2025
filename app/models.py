from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MUFData(BaseModel):
    roquetes: Optional[float]
    arenosillo: Optional[float]
    avg: Optional[float]
    ts: datetime
    status: str  # "OK" or "STALE"


class MUFSeries(BaseModel):
    timestamps: list[datetime]
    roquetes: list[Optional[float]]
    arenosillo: list[Optional[float]]
    avg: list[Optional[float]]


class StationData(BaseModel):
    name: str
    latitude: float
    longitude: float
    mufd: Optional[float] = None
    timestamp: Optional[datetime] = None


class DXSpot(BaseModel):
    spotter: str  # Indicatif de la station qui fait le spot
    dx_call: str  # Indicatif de la station spottée
    frequency: float  # Fréquence en kHz
    comment: str  # Commentaire du spot
    time: datetime  # Heure du spot
    country_spotter: Optional[str] = None  # Pays du spotter
    country_dx: Optional[str] = None  # Pays de la station spottée


class DXSpotList(BaseModel):
    spots: list[DXSpot]
    last_update: datetime
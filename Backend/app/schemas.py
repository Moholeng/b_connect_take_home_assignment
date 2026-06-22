"""Pydantic models describing the API response shapes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, IPvAnyAddress

class ORMModel(BaseModel):
    """Base model that reads attributes directly from ORM instances."""

    model_config = ConfigDict(from_attributes=True)

class SessionOut(ORMModel):
    """A Wi-Fi session as returned by the API."""

    id: UUID
    external_id: str
    access_point_id: UUID
    client_mac: str
    username: str | None
    device_type: str | None
    os: str | None
    gender: str | None
    age: int | None
    ssid: str | None
    ip_assigned: IPvAnyAddress | None
    start_time: datetime
    end_time: datetime | None
    duration_seconds: int | None
    rx_bytes: int | None
    tx_bytes: int | None
    signal_dbm: int | None

class AccessPointOut(ORMModel):
    """An access point, optionally nested under its venue."""

    id: UUID
    external_id: str
    venue_id: UUID
    name: str
    mac_address: str
    model: str | None
    ip_address: IPvAnyAddress | None
    firmware: str | None
    status: str
    uptime_seconds: int | None 

class VenueOut(ORMModel):

    id: UUID
    external_id: str
    name: str
    address: str | None
    city: str | None
    country: str | None
    timezone: str | None
    latitude: float | None
    longitude: float | None
    access_points: list[AccessPointOut] = []

class SyncLogOut(ORMModel):
    """A sync-run audit record."""

    id: UUID
    status: str
    source: str | None
    started_at: datetime
    finished_at: datetime | None
    venues_synced: int | None
    access_points_synced: int | None
    sessions_synced: int | None
    error_message: str | None

class SessionPage(BaseModel):
    """Paginated wrapper for the session list."""

    total: int
    limit: int
    offset: int
    items: list[SessionOut]
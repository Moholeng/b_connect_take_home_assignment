"""ORM models mapped to the existing Supabase tables.

The tables are created by schema.sql, so the application does not run
``create_all``. Server-side defaults and the ``set_updated_at`` trigger
keep ``id``, ``created_at``, and ``updated_at`` populated automatically.
"""

import uuid

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Venue(Base):
    """A physical location reported by the Wi-Fi controller."""

    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    external_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    timezone: Mapped[str | None] = mapped_column(String)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    access_points: Mapped[list["AccessPoint"]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )


class AccessPoint(Base):
    """A hardware access point, uniquely identified by its MAC address."""

    __tablename__ = "access_points"
    __table_args__ = (UniqueConstraint("mac_address", name="uq_access_points_mac"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    external_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venues.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    mac_address: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str | None] = mapped_column(String)
    ip_address: Mapped[str | None] = mapped_column(INET)
    firmware: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="online")
    uptime_seconds: Mapped[int | None] = mapped_column(BigInteger, default=0)
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    venue: Mapped["Venue"] = relationship(back_populates="access_points")
    sessions: Mapped[list["WifiSession"]] = relationship(
        back_populates="access_point", cascade="all, delete-orphan"
    )


class WifiSession(Base):
    """A single client Wi-Fi session attached to an access point."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    external_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    access_point_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("access_points.id", ondelete="CASCADE"),
        nullable=False,
    )
    client_mac: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str | None] = mapped_column(String)
    device_type: Mapped[str | None] = mapped_column(String)
    os: Mapped[str | None] = mapped_column(String)
    gender: Mapped[str | None] = mapped_column(String)
    age: Mapped[int | None] = mapped_column(Integer)
    ssid: Mapped[str | None] = mapped_column(String)
    ip_assigned: Mapped[str | None] = mapped_column(INET)
    start_time: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    rx_bytes: Mapped[int | None] = mapped_column(BigInteger, default=0)
    tx_bytes: Mapped[int | None] = mapped_column(BigInteger, default=0)
    signal_dbm: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    access_point: Mapped["AccessPoint"] = relationship(back_populates="sessions")


class SyncLog(Base):
    """Audit record for one ingestion run from the mock controller."""

    __tablename__ = "sync_logs"
    __table_args__ = (
        CheckConstraint(
            "status in ('success', 'partial', 'error')", name="sync_logs_status_check"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str | None] = mapped_column(String)
    started_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True))
    venues_synced: Mapped[int | None] = mapped_column(Integer, default=0)
    access_points_synced: Mapped[int | None] = mapped_column(Integer, default=0)
    sessions_synced: Mapped[int | None] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
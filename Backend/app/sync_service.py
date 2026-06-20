"""Idempotent ingestion of controller data into the database.

Each entity is upserted on its controller-supplied ``external_id`` using
PostgreSQL ``ON CONFLICT``, so running a sync repeatedly updates existing
rows instead of creating duplicates. Every run is recorded in sync_logs.
"""

from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.mock_controller import ControllerError, fetch_controller_data
from app.models import AccessPoint, SyncLog, Venue, WifiSession


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp (``Z`` suffix allowed) into a datetime."""
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _upsert(db: Session, model, values: dict, update_cols: list[str]):
    """Insert or update a row keyed on ``external_id`` and return its id."""
    stmt = pg_insert(model).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id"],
        set_={col: getattr(stmt.excluded, col) for col in update_cols},
    ).returning(model.id)
    return db.execute(stmt).scalar_one()


def run_sync(db: Session, simulate_failure: bool = False) -> SyncLog:
    """Fetch the controller payload, ingest it, and log the outcome.

    Returns the persisted ``SyncLog`` row. On failure the error is recorded
    as a sync log with status ``error`` and the exception is re-raised.
    """
    started_at = datetime.now(timezone.utc)

    try:
        payload = fetch_controller_data(simulate_failure=simulate_failure)
        venues = payload.get("venues", [])
        venue_count = ap_count = session_count = 0

        for venue in venues:
            venue_id = _upsert(
                db,
                Venue,
                {
                    "external_id": venue["venue_id"],
                    "name": venue["name"],
                    "address": venue.get("address"),
                    "city": venue.get("city"),
                    "country": venue.get("country"),
                    "timezone": venue.get("timezone"),
                    "latitude": venue.get("latitude"),
                    "longitude": venue.get("longitude"),
                },
                update_cols=[
                    "name",
                    "address",
                    "city",
                    "country",
                    "timezone",
                    "latitude",
                    "longitude",
                ],
            )
            venue_count += 1

            for ap in venue.get("access_points", []):
                access_point_id = _upsert(
                    db,
                    AccessPoint,
                    {
                        "external_id": ap["ap_id"],
                        "venue_id": venue_id,
                        "name": ap["name"],
                        "mac_address": ap["mac_address"],
                        "model": ap.get("model"),
                        "ip_address": ap.get("ip_address"),
                        "firmware": ap.get("firmware"),
                        "status": ap.get("status", "online"),
                        "uptime_seconds": ap.get("uptime_seconds", 0),
                    },
                    update_cols=[
                        "venue_id",
                        "name",
                        "mac_address",
                        "model",
                        "ip_address",
                        "firmware",
                        "status",
                        "uptime_seconds",
                    ],
                )
                ap_count += 1

                for session in ap.get("sessions", []):
                    _upsert(
                        db,
                        WifiSession,
                        {
                            "external_id": session["session_id"],
                            "access_point_id": access_point_id,
                            "client_mac": session["client_mac"],
                            "username": session.get("username"),
                            "device_type": session.get("device_type"),
                            "os": session.get("os"),
                            "gender": session.get("gender"),
                            "age": session.get("age"),
                            "ssid": session.get("ssid"),
                            "ip_assigned": session.get("ip_assigned"),
                            "start_time": _parse_dt(session["start_time"]),
                            "end_time": _parse_dt(session.get("end_time")),
                            "duration_seconds": session.get("duration_seconds"),
                            "rx_bytes": session.get("rx_bytes", 0),
                            "tx_bytes": session.get("tx_bytes", 0),
                            "signal_dbm": session.get("signal_dbm"),
                        },
                        update_cols=[
                            "access_point_id",
                            "client_mac",
                            "username",
                            "device_type",
                            "os",
                            "gender",
                            "age",
                            "ssid",
                            "ip_assigned",
                            "start_time",
                            "end_time",
                            "duration_seconds",
                            "rx_bytes",
                            "tx_bytes",
                            "signal_dbm",
                        ],
                    )
                    session_count += 1

        log = SyncLog(
            status="success",
            source=payload.get("controller", "mywifinetworks-mock"),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            venues_synced=venue_count,
            access_points_synced=ap_count,
            sessions_synced=session_count,
            raw_payload=payload,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    except (ControllerError, Exception) as exc:
        db.rollback()
        log = SyncLog(
            status="error",
            source="mywifinetworks-mock",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            venues_synced=0,
            access_points_synced=0,
            sessions_synced=0,
            error_message=str(exc),
        )
        db.add(log)
        db.commit()
        raise
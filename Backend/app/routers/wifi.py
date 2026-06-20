"""Read endpoints for synced venues and Wi-Fi sessions."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import AccessPoint, Venue, WifiSession
from app.schemas import SessionPage, VenueOut

router = APIRouter(tags=["wifi"])


@router.get("/venues", response_model=list[VenueOut])
def list_venues(db: Session = Depends(get_db)):
    """List all synced venues with their access points."""
    stmt = (
        select(Venue)
        .options(selectinload(Venue.access_points))
        .order_by(Venue.name)
    )
    return db.execute(stmt).scalars().all()


@router.get("/sessions", response_model=SessionPage)
def list_sessions(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    active_only: bool = False,
    venue_id: str | None = None,
):
    """List Wi-Fi sessions with pagination and optional filters.

    Args:
        limit: Page size (1-200).
        offset: Number of rows to skip.
        active_only: When True, return only sessions with no end_time.
        venue_id: Filter to a single venue's external_id (e.g. ``VEN-001``).
    """
    filters = []
    if active_only:
        filters.append(WifiSession.end_time.is_(None))
    if venue_id is not None:
        filters.append(Venue.external_id == venue_id)

    base = (
        select(WifiSession)
        .join(AccessPoint, WifiSession.access_point_id == AccessPoint.id)
        .join(Venue, AccessPoint.venue_id == Venue.id)
    )
    for condition in filters:
        base = base.where(condition)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = db.execute(count_stmt).scalar_one()

    page_stmt = base.order_by(WifiSession.start_time.desc()).limit(limit).offset(offset)
    items = db.execute(page_stmt).scalars().all()

    return SessionPage(total=total, limit=limit, offset=offset, items=items)
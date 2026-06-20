"""Sync endpoints: trigger a sync and read the latest sync status."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SyncLog
from app.schemas import SyncLogOut
from app.sync_service import run_sync

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncLogOut)
def trigger_sync(simulate_failure: bool = False, db: Session = Depends(get_db)):
    """Trigger a sync from the mock controller and return the run record."""
    try:
        return run_sync(db, simulate_failure=simulate_failure)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sync failed: {exc}",
        ) from exc


@router.get("/sync-status", response_model=SyncLogOut | None)
def get_sync_status(db: Session = Depends(get_db)):
    """Return the most recent sync run, or null if no sync has run yet."""
    stmt = select(SyncLog).order_by(SyncLog.started_at.desc()).limit(1)
    return db.execute(stmt).scalar_one_or_none()
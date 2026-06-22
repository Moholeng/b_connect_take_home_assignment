"""AI-generated network insights endpoint."""

import json

import openai
from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AccessPoint, Venue, WifiSession

router = APIRouter(tags=["insights"])

MODEL = "gpt-4o-mini"

# Strict instruction: exactly three bullets, no preamble.
SYSTEM_PROMPT = (
    "You are a network and venue analyst for a Wi-Fi monitoring platform. "
    "You are given a JSON summary of the current venues and Wi-Fi sessions. "
    "Respond with EXACTLY three concise bullet points summarising current "
    "network activity — for example the busiest venue, active-session levels, "
    "or unusual data-usage spikes. Each bullet must start with '- '. "
    "No preamble, no closing remarks, never more than three bullets."
)


class InsightsOut(BaseModel):
    """The AI summary returned to the frontend."""

    insights: str
    model: str


def _build_summary(db: Session) -> dict:
    """Aggregate per-venue session activity into a compact dict for the model."""
    stmt = (
        select(
            Venue.name,
            Venue.city,
            func.count(WifiSession.id).label("total_sessions"),
            func.count(WifiSession.id)
            .filter(WifiSession.end_time.is_(None))
            .label("active_sessions"),
            func.coalesce(
                func.sum(
                    func.coalesce(WifiSession.rx_bytes, 0)
                    + func.coalesce(WifiSession.tx_bytes, 0)
                ),
                0,
            ).label("total_bytes"),
        )
        .join(AccessPoint, AccessPoint.venue_id == Venue.id)
        .join(WifiSession, WifiSession.access_point_id == AccessPoint.id)
        .group_by(Venue.id, Venue.name, Venue.city)
        .order_by(func.count(WifiSession.id).desc())
    )

    venues = [
        {
            "venue": name,
            "city": city,
            "total_sessions": total,
            "active_sessions": active,
            "total_mb": round(float(total_bytes) / 1_000_000, 1),
        }
        for name, city, total, active, total_bytes in db.execute(stmt).all()
    ]

    return {
        "venue_count": len(venues),
        "total_sessions": sum(v["total_sessions"] for v in venues),
        "active_sessions": sum(v["active_sessions"] for v in venues),
        "venues": venues,
    }


@router.get("/insights", response_model=InsightsOut)
def get_insights(db: Session = Depends(get_db)):
    """Summarise current venues + sessions and ask the model for 3 insights."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key is not configured.",
        )

    summary = _build_summary(db)
    if not summary["venues"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No synced data yet — run a sync before generating insights.",
        )

    try:
        # timeout on the client so a slow API call can't hang the request.
        client = OpenAI(api_key=settings.openai_api_key, timeout=20.0)
        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.3,
            max_tokens=300,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(summary, default=str)},
            ],
        )
        text = (completion.choices[0].message.content or "").strip()
    except openai.APITimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI request timed out. Please try again.",
        ) from exc
    except openai.OpenAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI request failed: {exc}",
        ) from exc

    if not text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI returned an empty response.",
        )

    return InsightsOut(insights=text, model=MODEL)
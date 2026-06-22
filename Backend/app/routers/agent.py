"""Interactive chat agent backed by OpenAI function calling.

The model never sees or writes SQL. It can only invoke the curated,
read-only SQLAlchemy functions registered in TOOL_FUNCTIONS below.
"""

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

router = APIRouter(tags=["agent"])

MODEL = "gpt-4o-mini"
MAX_TOOL_ROUNDS = 5  # safety cap so the tool loop can never run forever

SYSTEM_PROMPT = (
    "Your name is b-ingo"
    "You are the b-connect Wi-Fi network assistant. Answer questions about "
    "venues and Wi-Fi sessions using ONLY the provided tools. Never invent "
    "data — if the tools don't cover the question, say you don't have that "
    "information. Keep answers concise and friendly."
)


# ── Tool functions (read-only, the ONLY way the model touches the DB) ──────

def get_all_venues(db: Session) -> dict:
    """Return every venue with its city and country."""
    rows = db.execute(
        select(Venue.name, Venue.city, Venue.country).order_by(Venue.name)
    ).all()
    return {"venues": [{"name": n, "city": c, "country": co} for n, c, co in rows]}


def get_active_sessions_count(db: Session, venue_name: str | None = None) -> dict:
    """Count active sessions (no end_time), optionally filtered by venue name."""
    stmt = (
        select(func.count(WifiSession.id))
        .join(AccessPoint, WifiSession.access_point_id == AccessPoint.id)
        .join(Venue, AccessPoint.venue_id == Venue.id)
        .where(WifiSession.end_time.is_(None))
    )
    if venue_name:
        stmt = stmt.where(Venue.name.ilike(f"%{venue_name}%"))
    count = db.execute(stmt).scalar_one()
    return {"venue_name": venue_name, "active_sessions": count}


def get_demographics_summary(db: Session) -> dict:
    """Return a gender breakdown and average age across all sessions."""
    gender_rows = db.execute(
        select(WifiSession.gender, func.count())
        .group_by(WifiSession.gender)
    ).all()
    avg_age = db.execute(select(func.avg(WifiSession.age))).scalar()
    return {
        "by_gender": {(g or "unknown"): n for g, n in gender_rows},
        "average_age": round(float(avg_age), 1) if avg_age is not None else None,
    }


# Map tool name -> callable. Each takes (db, parsed_args_dict).
TOOL_FUNCTIONS = {
    "get_all_venues": lambda db, args: get_all_venues(db),
    "get_active_sessions_count": lambda db, args: get_active_sessions_count(
        db, args.get("venue_name")
    ),
    "get_demographics_summary": lambda db, args: get_demographics_summary(db),
}

# Tool schemas advertised to the model.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_venues",
            "description": "List all venues with their city and country.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_sessions_count",
            "description": (
                "Count currently active Wi-Fi sessions. Optionally filter by "
                "a venue name (partial match)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_name": {
                        "type": "string",
                        "description": "Optional venue name to filter by.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_demographics_summary",
            "description": "Gender breakdown and average age across all sessions.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Run one chat turn through the model + tool-calling loop."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key is not configured.",
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message},
    ]

    try:
        client = OpenAI(api_key=settings.openai_api_key, timeout=30.0)

        for _ in range(MAX_TOOL_ROUNDS):
            completion = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                temperature=0.2,
            )
            msg = completion.choices[0].message

            # No tool call -> the model has its final answer.
            if not msg.tool_calls:
                return ChatResponse(reply=(msg.content or "").strip())

            # Otherwise: record the assistant turn, run each tool, feed results back.
            messages.append(msg)  # the SDK message object is accepted as-is
            for call in msg.tool_calls:
                fn = TOOL_FUNCTIONS.get(call.function.name)
                args = json.loads(call.function.arguments or "{}")
                result = fn(db, args) if fn else {"error": "unknown tool"}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

        # Loop exhausted without a final answer.
        return ChatResponse(
            reply="Sorry, I couldn't complete that request. Please try rephrasing."
        )

    except openai.RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The AI is rate-limited right now. Please try again shortly.",
        ) from exc
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
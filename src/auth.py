"""Fail-closed Firebase ID token verification."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import AsyncSessionLocal, Coach

FIREBASE_PROJECT_ID = (
    os.environ.get("FIREBASE_PROJECT_ID")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or "fitai-54f2c"
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


def verify_bearer_token(token: str) -> dict:
    """Verify a Firebase ID token without requiring Application Default Credentials."""
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token as google_id_token

        decoded = google_id_token.verify_firebase_token(
            token,
            GoogleRequest(),
            audience=FIREBASE_PROJECT_ID,
        )
        if not decoded:
            raise HTTPException(status_code=401, detail="Invalid Firebase token")
        return decoded
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {exc}") from exc


async def get_current_coach(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> Coach:
    authorization = authorization or request.headers.get("authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    decoded = verify_bearer_token(token)
    uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token missing uid")
    name = decoded.get("name")
    email = decoded.get("email")

    result = await db.execute(select(Coach).where(Coach.firebase_uid == uid))
    coach = result.scalar_one_or_none()
    if coach is None:
        coach = Coach(firebase_uid=uid, name=name, email=email)
        db.add(coach)
        await db.commit()
        await db.refresh(coach)
    elif name and coach.name != name:
        coach.name = name
        coach.email = email
        await db.commit()
        await db.refresh(coach)
    return coach

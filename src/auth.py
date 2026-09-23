"""Fail-closed Firebase ID token verification + admin gate sessions."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
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

ADMIN_EMAILS = {
    e.strip().lower()
    for e in (os.environ.get("ADMIN_EMAILS") or "").split(",")
    if e.strip()
}

ADMIN_GATE_SECRET = (os.environ.get("ADMIN_GATE_SECRET") or "").strip()
ADMIN_SESSION_TTL_SEC = int(os.environ.get("ADMIN_SESSION_TTL_SEC") or 8 * 3600)


def _apply_admin_flag(coach: Coach, email: Optional[str]) -> bool:
    if not email:
        return bool(coach.is_admin)
    normalized = email.strip().lower()
    if normalized in ADMIN_EMAILS:
        return True
    return bool(coach.is_admin)


def admin_gate_configured() -> bool:
    return bool(ADMIN_GATE_SECRET)


def verify_admin_gate_secret(gate_secret: Optional[str]) -> None:
    if not ADMIN_GATE_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Admin gate is not configured. Set ADMIN_GATE_SECRET on the API.",
        )
    if not gate_secret or not hmac.compare_digest(str(gate_secret), ADMIN_GATE_SECRET):
        raise HTTPException(status_code=401, detail="Invalid admin gate key")


def mint_admin_session_token(coach_id: int) -> tuple[str, int]:
    if not ADMIN_GATE_SECRET:
        raise HTTPException(status_code=503, detail="Admin gate is not configured")
    expires_at = int(time.time()) + ADMIN_SESSION_TTL_SEC
    payload = f"{int(coach_id)}:{expires_at}"
    sig = hmac.new(
        ADMIN_GATE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{sig}", expires_at


def verify_admin_session_token(token: Optional[str], coach_id: int) -> bool:
    if not token or not ADMIN_GATE_SECRET:
        return False
    parts = str(token).split(":")
    if len(parts) != 3:
        return False
    cid_raw, exp_raw, sig = parts
    try:
        cid = int(cid_raw)
        exp = int(exp_raw)
    except ValueError:
        return False
    if cid != int(coach_id) or exp < int(time.time()):
        return False
    payload = f"{cid}:{exp}"
    expected = hmac.new(
        ADMIN_GATE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(sig, expected)


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
        is_admin = bool(email and email.strip().lower() in ADMIN_EMAILS)
        coach = Coach(firebase_uid=uid, name=name, email=email, is_admin=is_admin)
        db.add(coach)
        await db.commit()
        await db.refresh(coach)
    else:
        changed = False
        if name and coach.name != name:
            coach.name = name
            changed = True
        if email and coach.email != email:
            coach.email = email
            changed = True
        admin_now = _apply_admin_flag(coach, email or coach.email)
        if coach.is_admin != admin_now:
            coach.is_admin = admin_now
            changed = True
        if changed:
            await db.commit()
            await db.refresh(coach)
    return coach


async def get_current_admin(
    request: Request,
    coach: Coach = Depends(get_current_coach),
    x_admin_session: Optional[str] = Header(default=None, alias="X-Admin-Session"),
) -> Coach:
    """Admin APIs require coach.is_admin PLUS a valid admin-gate session token."""
    if not coach.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    session = x_admin_session or request.headers.get("x-admin-session")
    if not verify_admin_session_token(session, coach.id):
        raise HTTPException(
            status_code=401,
            detail="Admin session required. Sign in at /admin/login",
        )
    return coach

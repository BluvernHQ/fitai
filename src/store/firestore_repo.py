"""Optional Firestore mirror. SQL remains default until DATA_STORE=firestore."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

_client = None


def data_store() -> str:
    return (os.environ.get("DATA_STORE") or "sql").strip().lower()


def firestore_enabled() -> bool:
    return data_store() in {"dual", "firestore"}


def _db():
    global _client
    if _client is not None:
        return _client
    import firebase_admin
    from firebase_admin import firestore

    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.exists(cred_path):
            from firebase_admin import credentials

            firebase_admin.initialize_app(credentials.Certificate(cred_path))
        else:
            firebase_admin.initialize_app()
    database_id = os.environ.get("FIRESTORE_DATABASE") or "(default)"
    _client = firestore.client(database_id=database_id) if database_id != "(default)" else firestore.client()
    return _client


def _now():
    return datetime.now(timezone.utc).isoformat()


def mirror_coach(uid: str, payload: dict[str, Any]) -> None:
    if not firestore_enabled():
        return
    try:
        _db().collection("coaches").document(str(uid)).set({**payload, "updated_at": _now()}, merge=True)
    except Exception as exc:
        print(f"firestore coach mirror skipped: {exc}")


def mirror_athlete(uid: str, athlete_id: str, payload: dict[str, Any]) -> None:
    if not firestore_enabled():
        return
    try:
        _db().collection("coaches").document(str(uid)).collection("athletes").document(str(athlete_id)).set(
            {**payload, "updated_at": _now(), "legacy_id": athlete_id},
            merge=True,
        )
    except Exception as exc:
        print(f"firestore athlete mirror skipped: {exc}")


def mirror_program(uid: str, athlete_id: str, program_id: str, payload: dict[str, Any]) -> None:
    if not firestore_enabled():
        return
    try:
        (
            _db()
            .collection("coaches")
            .document(str(uid))
            .collection("athletes")
            .document(str(athlete_id))
            .collection("programs")
            .document(str(program_id))
            .set({**payload, "updated_at": _now(), "legacy_id": program_id}, merge=True)
        )
    except Exception as ext:
        print(f"firestore program mirror skipped: {ext}")


def get_public_share(token_hash: str) -> Optional[dict]:
    if data_store() != "firestore":
        return None
    snap = _db().collection("shares").document(token_hash).get()
    return snap.to_dict() if snap.exists else None

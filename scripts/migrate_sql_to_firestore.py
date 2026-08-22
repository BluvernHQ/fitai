#!/usr/bin/env python3
"""Export SQLAlchemy rows to Firestore. Idempotent via legacy_id."""

from __future__ import annotations

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database import AsyncSessionLocal, Coach, Student, Assessment, ProgramDraft, PreferenceEvent
from src.store.firestore_repo import mirror_athlete, mirror_coach, mirror_program


async def main():
    os.environ.setdefault("DATA_STORE", "dual")
    async with AsyncSessionLocal() as db:
        coaches = (await db.execute(select(Coach))).scalars().all()
        for coach in coaches:
            mirror_coach(coach.firebase_uid, {"name": coach.name, "email": coach.email, "legacy_id": coach.id})
            students = (
                await db.execute(select(Student).where(Student.coach_id == coach.id))
            ).scalars().all()
            for student in students:
                mirror_athlete(
                    coach.firebase_uid,
                    str(student.id),
                    {"name": student.name, "days_per_week": student.days_per_week, "legacy_id": student.id},
                )
                programs = (
                    await db.execute(select(ProgramDraft).where(ProgramDraft.student_id == student.id))
                ).scalars().all()
                for program in programs:
                    mirror_program(
                        coach.firebase_uid,
                        str(student.id),
                        str(program.id),
                        {"status": program.status, "week_index": program.week_index or 1, "legacy_id": program.id},
                    )
    print("Migration dry-run/write complete")


if __name__ == "__main__":
    asyncio.run(main())

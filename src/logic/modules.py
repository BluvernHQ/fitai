"""Platform module catalog — plug-and-play feature registry."""

from __future__ import annotations

from typing import Any

MODULE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "coach-insights",
        "name": "Coach Learning",
        "description": "Taste priors from keep/replace decisions. Never overrides safety or kit gates.",
        "category": "coach",
        "scope": "coach",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "fms-assessment",
        "name": "FMS Assessment",
        "description": "Seven-screen movement screen with rules-first scoring.",
        "category": "coach",
        "scope": "coach",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "program-editor",
        "name": "Program Editor",
        "description": "Calendar week view, swap candidates, edit loads, approve and share.",
        "category": "coach",
        "scope": "coach",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "athlete-share",
        "name": "Athlete Share",
        "description": "Read-only public links for approved weeks.",
        "category": "coach",
        "scope": "coach",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "lift-max-log",
        "name": "1RM History",
        "description": "Append-only strength log on student profile.",
        "category": "coach",
        "scope": "coach",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "admin-dashboard",
        "name": "Admin Dashboard",
        "description": "Platform overview, coach counts, program volume.",
        "category": "admin",
        "scope": "admin",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "module-manager",
        "name": "Module Manager",
        "description": "Enable or disable platform features plug-and-play.",
        "category": "admin",
        "scope": "admin",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "system-health",
        "name": "System Health",
        "description": "API status, database, Groq and Firebase connectivity.",
        "category": "admin",
        "scope": "admin",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "coach-roster-admin",
        "name": "Coach Roster",
        "description": "All coaches, student counts, admin promotion.",
        "category": "admin",
        "scope": "admin",
        "default_enabled": True,
        "version": "1.0.0",
    },
    {
        "id": "analytics",
        "name": "Analytics",
        "description": "FMS trends, block completion, strength progression charts.",
        "category": "platform",
        "scope": "coach",
        "default_enabled": False,
        "version": "0.1.0",
    },
    {
        "id": "recovery-programming",
        "name": "Recovery Programming",
        "description": "Programmed active recovery sessions (not notes only).",
        "category": "platform",
        "scope": "coach",
        "default_enabled": False,
        "version": "0.1.0",
    },
]

CATALOG_BY_ID = {m["id"]: m for m in MODULE_CATALOG}

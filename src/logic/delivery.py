"""Export helpers: athlete DTO, XLSX, HTML/PDF."""

from __future__ import annotations

import hashlib
import io
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def mint_share_token() -> str:
    return secrets.token_urlsafe(24)


def athlete_dto(plan: dict) -> dict:
    """Strip coach-only fields from an approved week JSON."""
    days = []
    for day in plan.get("days") or []:
        blocks = {}
        for key, items in (day.get("blocks") or {}).items():
            if not isinstance(items, list):
                continue
            clean = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                clean.append(
                    {
                        "exercise_id": item.get("exercise_id"),
                        "name": item.get("name"),
                        "role": item.get("role") or item.get("tag"),
                        "section": item.get("section") or key,
                        "sets": item.get("sets"),
                        "reps": item.get("reps"),
                        "rpe": item.get("rpe"),
                        "reps_rpe": item.get("reps_rpe"),
                        "percent_1rm": item.get("percent_1rm"),
                        "load": item.get("load") or item.get("load_kg"),
                        "rest": item.get("rest"),
                        "tempo": item.get("tempo"),
                        "coach_note": item.get("coach_note"),
                        "unfilled": item.get("unfilled", False),
                    }
                )
            blocks[key] = clean
        days.append(
            {
                "day": day.get("day"),
                "title": day.get("title"),
                "emphasis": day.get("emphasis") or [],
                "session_kind": day.get("session_kind"),
                "blocks": blocks,
                "block_meta": day.get("block_meta") or {},
            }
        )
    return {
        "schema_version": plan.get("schema_version"),
        "week_title": plan.get("week_title"),
        "week_type": plan.get("week_type"),
        "week_index": plan.get("week_index"),
        "needs_summary": plan.get("needs_summary"),
        "status": plan.get("status"),
        "referral": plan.get("referral", False),
        "days": days,
        "calendar": [
            {k: cell.get(k) for k in ("weekday", "kind", "tone", "label", "day", "title", "notes", "done")}
            for cell in (plan.get("calendar") or [])
        ],
        "ui": plan.get("ui") or {},
        "mesocycle": {
            k: (plan.get("mesocycle") or {}).get(k)
            for k in ("length", "week_index", "phase", "retest_due")
        },
    }


def default_expiry(days: int = 21) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def plan_to_xlsx_bytes(plan: dict) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Program"
    ws.append(
        ["Day", "Title", "Section", "Role", "Exercise", "Sets", "Reps-RPE", "%1RM", "Load", "Rest", "Why"]
    )
    section_order = (plan.get("ui") or {}).get("section_order") or [
        "ramp",
        "activation",
        "block_a",
        "block_b",
        "accessories",
    ]
    for day in plan.get("days") or []:
        meta = day.get("block_meta") or {}
        for section in section_order:
            label = (meta.get(section) or {}).get("label") or section
            for item in day.get("blocks", {}).get(section) or []:
                ws.append(
                    [
                        day.get("day"),
                        day.get("title"),
                        label,
                        item.get("role") or item.get("tag"),
                        item.get("name"),
                        item.get("sets"),
                        item.get("reps_rpe"),
                        item.get("percent_1rm"),
                        item.get("load") or item.get("load_kg"),
                        item.get("rest"),
                        item.get("why") or item.get("coach_note"),
                    ]
                )
    cal = wb.create_sheet("Calendar")
    cal.append(["Weekday", "Kind", "Title", "Notes", "Done"])
    for cell in plan.get("calendar") or []:
        cal.append([cell.get("weekday"), cell.get("kind"), cell.get("title"), cell.get("notes"), cell.get("done")])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def plan_to_html(plan: dict, *, athlete: bool = False) -> str:
    title = plan.get("week_title") or "FitAI Program"
    rows = []
    section_order = (plan.get("ui") or {}).get("section_order") or [
        "ramp",
        "activation",
        "block_a",
        "block_b",
        "accessories",
    ]
    for day in plan.get("days") or []:
        rows.append(f"<h2>Day {day.get('day')}: {day.get('title') or ''}</h2>")
        meta = day.get("block_meta") or {}
        for section in section_order:
            items = day.get("blocks", {}).get(section) or []
            if not items:
                continue
            label = (meta.get(section) or {}).get("label") or section
            rows.append(f"<h3>{label}</h3><table><thead><tr><th>Role</th><th>Exercise</th><th>Sets</th><th>Reps-RPE</th><th>Load</th><th>Rest</th></tr></thead><tbody>")
            for item in items:
                rows.append(
                    "<tr>"
                    f"<td>{item.get('role') or ''}</td>"
                    f"<td>{item.get('name') or ''}</td>"
                    f"<td>{item.get('sets') or ''}</td>"
                    f"<td>{item.get('reps_rpe') or ''}</td>"
                    f"<td>{item.get('load') or item.get('load_kg') or '—'}</td>"
                    f"<td>{item.get('rest') or ''}</td>"
                    "</tr>"
                )
            rows.append("</tbody></table>")
    cal_rows = "".join(
        f"<tr><td>{c.get('weekday')}</td><td>{c.get('kind')}</td><td>{c.get('title') or ''}</td><td>{c.get('notes') or ''}</td></tr>"
        for c in (plan.get("calendar") or [])
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
body {{ font-family: Helvetica, Arial, sans-serif; color: #111; margin: 24px; }}
h1 {{ font-size: 22px; }} h2 {{ font-size: 16px; margin-top: 24px; }} h3 {{ font-size: 13px; color: #3f3; background: #111; color: #b6ff3b; padding: 6px 8px; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 12px; }}
th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
.meta {{ color: #555; margin-bottom: 16px; }}
@media print {{ button {{ display: none; }} }}
</style></head>
<body>
<button onclick="window.print()">Print / Save as PDF</button>
<h1>{title}</h1>
<p class="meta">{plan.get('needs_summary') or ''}</p>
<table><thead><tr><th>Day</th><th>Kind</th><th>Title</th><th>Notes</th></tr></thead><tbody>{cal_rows}</tbody></table>
{''.join(rows)}
<p class="meta">FitAI · {'athlete view' if athlete else 'coach copy'}</p>
</body></html>"""


def plan_to_pdf_bytes(plan: dict) -> Optional[bytes]:
    html = plan_to_html(plan)
    try:
        from weasyprint import HTML

        return HTML(string=html).write_pdf()
    except Exception:
        return None

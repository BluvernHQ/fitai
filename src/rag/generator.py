"""Optional Groq rewrite of coach notes. Never invents exercises or dosage."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def enrich_coach_notes(plan: dict[str, Any], comments: dict | None = None) -> dict[str, Any]:
    if plan.get("referral"):
        return plan
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return plan
    try:
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import JsonOutputParser

        by_id = {}
        for day in plan.get("days", []):
            for items in day.get("blocks", {}).values():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if isinstance(item, dict) and item.get("exercise_id") and not item.get("unfilled"):
                        by_id[item["exercise_id"]] = {
                            "name": item.get("name"),
                            "coach_note": item.get("coach_note"),
                            "why": item.get("why"),
                        }
        if not by_id:
            return plan
        llm = ChatGroq(
            model_name=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=0.2,
            api_key=api_key,
        )
        parser = JsonOutputParser()
        prompt = ChatPromptTemplate.from_template(
            """Rewrite needs_summary and one cue per exercise_id.
Use ONLY these ids: {ids}
Facts (do not add exercises, sets, loads, or diagnoses): {facts}
Assessor comments: {comments}
Needs: {needs}
Return JSON: {{"needs_summary": str, "notes": {{"<exercise_id>": "one cue"}}}}
If an id is unknown, omit it.
"""
        )
        chain = prompt | llm | parser
        result = chain.invoke(
            {
                "ids": ", ".join(by_id.keys()),
                "facts": by_id,
                "comments": comments or plan.get("analysis", {}).get("comments") or {},
                "needs": plan.get("needs_summary"),
            }
        )
        if not isinstance(result, dict):
            return plan
        if result.get("needs_summary"):
            plan["needs_summary"] = result["needs_summary"]
        notes = result.get("notes") or {}
        allowed = set(by_id)
        for day in plan.get("days", []):
            for items in day.get("blocks", {}).values():
                if not isinstance(items, list):
                    continue
                for item in items:
                    eid = item.get("exercise_id") if isinstance(item, dict) else None
                    if eid in allowed and eid in notes:
                        item["coach_note"] = str(notes[eid])[:400]
    except Exception as exc:
        print(f"Note enrichment skipped: {exc}")
    return plan

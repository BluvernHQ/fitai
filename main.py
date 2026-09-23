import json
import uvicorn
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import uuid

# ── IMPORTS ──
from src.logic.assessment_fusion import analyze_assessment_session, normalize_session
from src.logic.fms_analyzer import analyze_fms_profile
from src.logic.load_calculator import estimate_1rm, load_tables, percent_1rm_for, pro_rata_maxes, rm_ladder_loads
from src.logic.batteries import load_registry
from src.logic.prescription import assemble_weekly_program, catalog_by_id, load_methodology
from src.logic.periodization import apply_week_progression, mesocycle_envelope, template_for
from src.logic.taste import insights_payload, plans_differ_selection
from src.logic.modules import MODULE_CATALOG, CATALOG_BY_ID
from src.logic.delivery import (
    athlete_dto,
    default_expiry,
    hash_token,
    mint_share_token,
    plan_to_html,
    plan_to_pdf_bytes,
    plan_to_xlsx_bytes,
)
from src.rag.generator import enrich_coach_notes
from src.database import (
    AsyncSessionLocal,
    engine,
    Base,
    Coach,
    Student,
    LiftMax,
    LiftMaxLog,
    Assessment,
    ProgramDraft,
    PreferenceEvent,
    CoachExercisePrior,
    TrainingBlock,
    ShareLink,
    PlatformModule,
    DATABASE_URL,
)
from src.auth import (
    get_current_coach,
    get_current_admin,
    get_db,
    mint_admin_session_token,
    verify_admin_gate_secret,
    admin_gate_configured,
)
from src.store.firestore_repo import firestore_enabled, mirror_athlete, mirror_coach, mirror_program

# ────────────────────────────────────────────────
# Lifecycle (Startup)
# ────────────────────────────────────────────────
async def _ensure_schema():
    from sqlalchemy import text

    statements = [
        "ALTER TABLE program_drafts ADD COLUMN block_id INTEGER",
        "ALTER TABLE program_drafts ADD COLUMN week_index INTEGER DEFAULT 1",
        "ALTER TABLE program_drafts ADD COLUMN snapshot_immutable BOOLEAN DEFAULT 0",
        "ALTER TABLE preference_events ADD COLUMN event_id VARCHAR",
        "ALTER TABLE preference_events ADD COLUMN reason_code VARCHAR",
        "ALTER TABLE coaches ADD COLUMN is_admin BOOLEAN DEFAULT 0",
        "ALTER TABLE assessments ADD COLUMN assessment_kind VARCHAR DEFAULT 'baseline_session'",
        "ALTER TABLE assessments ADD COLUMN selected_batteries JSON",
        "ALTER TABLE assessments ADD COLUMN findings JSON",
    ]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass


async def _seed_platform_modules(db: AsyncSession):
    existing = (await db.execute(select(PlatformModule.module_id))).scalars().all()
    known = set(existing)
    for spec in MODULE_CATALOG:
        if spec["id"] in known:
            continue
        db.add(
            PlatformModule(
                module_id=spec["id"],
                enabled=bool(spec.get("default_enabled", True)),
                config={},
            )
        )
    await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FitAI API")
    await _ensure_schema()
    async with AsyncSessionLocal() as db:
        await _seed_platform_modules(db)
    print("Schema ready")
    yield

app = FastAPI(title="FMS Smart Coach API", version="4.0", lifespan=lifespan)

ROOT = Path(__file__).resolve().parent
FMS_SPEC_PATH = ROOT / "data/processed/fms_spec.json"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,https://fitai-54f2c.web.app,https://fitai-54f2c.firebaseapp.com").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/fms/spec")
def get_fms_spec():
    if not FMS_SPEC_PATH.exists():
        raise HTTPException(status_code=404, detail="FMS spec not found")
    return json.loads(FMS_SPEC_PATH.read_text(encoding="utf-8"))


@app.get("/methodology")
def get_methodology():
    return load_methodology()


# ────────────────────────────────────────────────
# Pydantic Models (Validation)
# ────────────────────────────────────────────────

# --- 1. DEEP SQUAT ---
class OS_TrunkTorso(BaseModel):
    upright_torso: int = 0
    excessive_forward_lean: int = 0
    rib_flare: int = 0
    lumbar_flexion: int = 0
    lumbar_extension_sway_back: int = 0

class OS_LowerLimb(BaseModel):
    knees_track_over_toes: int = 0
    knee_valgus: int = 0
    knee_varus: int = 0
    uneven_depth: int = 0

class OS_Feet(BaseModel):
    heels_stay_down: int = 0
    heels_lift: int = 0
    excessive_pronation: int = 0
    excessive_supination: int = 0

class OS_UpperBodyBarPosition(BaseModel):
    bar_aligned_over_mid_foot: int = 0
    bar_drifts_forward: int = 0
    arms_fall_forward: int = 0
    shoulder_mobility_restriction_suspected: int = 0

class OverheadSquatData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    trunk_torso: OS_TrunkTorso = Field(default_factory=OS_TrunkTorso)
    lower_limb: OS_LowerLimb = Field(default_factory=OS_LowerLimb)
    feet: OS_Feet = Field(default_factory=OS_Feet)
    upper_body_bar_position: OS_UpperBodyBarPosition = Field(default_factory=OS_UpperBodyBarPosition)

# --- 2. HURDLE STEP ---
class HS_PelvisCoreControl(BaseModel):
    pelvis_stable: int = 0
    pelvic_drop_trendelenburg: int = 0
    excessive_rotation: int = 0
    loss_of_balance: int = 0

class HS_StanceLeg(BaseModel):
    knee_stable: int = 0
    knee_valgus: int = 0
    knee_varus: int = 0
    ankle_instability: int = 0

class HS_SteppingLeg(BaseModel):
    clears_hurdle_smoothly: int = 0
    toe_drag: int = 0
    hip_flexion_restriction: int = 0
    asymmetrical_movement: int = 0

class HurdleStepData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    l_score: Optional[int] = None
    r_score: Optional[int] = None
    pelvis_core_control: HS_PelvisCoreControl = Field(default_factory=HS_PelvisCoreControl)
    stance_leg: HS_StanceLeg = Field(default_factory=HS_StanceLeg)
    stepping_leg: HS_SteppingLeg = Field(default_factory=HS_SteppingLeg)

# --- 3. INLINE LUNGE ---
class IL_Alignment(BaseModel):
    head_neutral: int = 0
    forward_head: int = 0
    trunk_upright: int = 0
    excessive_forward_lean: int = 0
    lateral_shift: int = 0

class IL_LowerBodyControl(BaseModel):
    knee_tracks_over_foot: int = 0
    knee_valgus: int = 0
    knee_instability: int = 0
    heel_lift: int = 0

class IL_BalanceStability(BaseModel):
    stable_throughout: int = 0
    wobbling: int = 0
    loss_of_balance: int = 0
    unequal_weight_distribution: int = 0

class InlineLungeData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    l_score: Optional[int] = None
    r_score: Optional[int] = None
    alignment: IL_Alignment = Field(default_factory=IL_Alignment)
    lower_body_control: IL_LowerBodyControl = Field(default_factory=IL_LowerBodyControl)
    balance_stability: IL_BalanceStability = Field(default_factory=IL_BalanceStability)

# --- 4. SHOULDER MOBILITY ---
class SM_ReachQuality(BaseModel):
    hands_within_fist_distance: int = 0
    hands_within_hand_length: int = 0
    excessive_gap: int = 0
    asymmetry_present: int = 0

class SM_Compensation(BaseModel):
    no_compensation: int = 0
    spine_flexion: int = 0
    rib_flare: int = 0
    scapular_winging: int = 0

class SM_Pain(BaseModel):
    no_pain: int = 0
    pain_reported: int = 0

class ShoulderMobilityData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    l_score: Optional[int] = None
    r_score: Optional[int] = None
    clearing_pain: bool = False
    reach_quality: SM_ReachQuality = Field(default_factory=SM_ReachQuality)
    compensation: SM_Compensation = Field(default_factory=SM_Compensation)
    pain: SM_Pain = Field(default_factory=SM_Pain)

# --- 5. ASLR ---
class ASLR_NonMovingLeg(BaseModel):
    remains_flat: int = 0
    knee_bends: int = 0
    hip_externally_rotates: int = 0
    foot_lifts_off_floor: int = 0

class ASLR_MovingLeg(BaseModel):
    gt_80_hip_flexion: int = 0
    between_60_80_hip_flexion: int = 0
    lt_60_hip_flexion: int = 0
    hamstring_restriction: int = 0

class ASLR_PelvicControl(BaseModel):
    pelvis_stable: int = 0
    anterior_tilt: int = 0
    posterior_tilt: int = 0

class ASLRData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    l_score: Optional[int] = None
    r_score: Optional[int] = None
    non_moving_leg: ASLR_NonMovingLeg = Field(default_factory=ASLR_NonMovingLeg)
    moving_leg: ASLR_MovingLeg = Field(default_factory=ASLR_MovingLeg)
    pelvic_control: ASLR_PelvicControl = Field(default_factory=ASLR_PelvicControl)

# --- 6. TRUNK STABILITY ---
class TSP_BodyAlignment(BaseModel):
    neutral_spine_maintained: int = 0
    sagging_hips: int = 0
    pike_position: int = 0

class TSP_CoreControl(BaseModel):
    initiates_as_one_unit: int = 0
    hips_lag: int = 0
    excessive_lumbar_extension: int = 0

class TSP_UpperBody(BaseModel):
    elbows_aligned: int = 0
    uneven_arm_push: int = 0
    shoulder_instability: int = 0

class TSPData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    clearing_pain: bool = False
    body_alignment: TSP_BodyAlignment = Field(default_factory=TSP_BodyAlignment)
    core_control: TSP_CoreControl = Field(default_factory=TSP_CoreControl)
    upper_body: TSP_UpperBody = Field(default_factory=TSP_UpperBody)

# --- 7. ROTARY STABILITY ---
class RS_DiagonalPattern(BaseModel):
    smooth_controlled: int = 0
    loss_of_balance: int = 0
    unable_to_complete: int = 0

class RS_SpinalControl(BaseModel):
    neutral_maintained: int = 0
    excessive_rotation: int = 0
    lumbar_shift: int = 0

class RS_Symmetry(BaseModel):
    symmetrical: int = 0
    left_side_deficit: int = 0
    right_side_deficit: int = 0

class RSData(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: Optional[int] = None
    comment: str = ""
    l_score: Optional[int] = None
    r_score: Optional[int] = None
    clearing_pain: bool = False
    diagonal_pattern: RS_DiagonalPattern = Field(default_factory=RS_DiagonalPattern)
    spinal_control: RS_SpinalControl = Field(default_factory=RS_SpinalControl)
    symmetry: RS_Symmetry = Field(default_factory=RS_Symmetry)

class FMSProfileRequest(BaseModel):
    """Legacy FMS-only body. Prefer AssessmentSessionRequest for modular batteries."""
    model_config = ConfigDict(extra="allow")
    overhead_squat: Optional[Dict[str, Any]] = None
    hurdle_step: Optional[Dict[str, Any]] = None
    inline_lunge: Optional[Dict[str, Any]] = None
    shoulder_mobility: Optional[Dict[str, Any]] = None
    active_straight_leg_raise: Optional[Dict[str, Any]] = None
    trunk_stability_pushup: Optional[Dict[str, Any]] = None
    rotary_stability: Optional[Dict[str, Any]] = None
    use_manual_scores: bool = False
    student_id: Optional[int] = None


class AssessmentSessionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    student_id: Optional[int] = None
    selected_batteries: Optional[List[str]] = None
    batteries: Optional[Dict[str, Any]] = None
    use_manual_scores: bool = False
    session_notes: Optional[str] = None
    athlete_context: Optional[Dict[str, Any]] = None


class LoadEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    load_kg: float
    reps: int
    rpe: float = 10
    anchor_lift: Optional[str] = "back_squat"
    include_pro_rata: bool = True


class CalculatedScores(BaseModel):
    overhead_squat: int
    hurdle_step: int
    inline_lunge: int
    shoulder_mobility: int
    active_straight_leg_raise: int
    trunk_stability_pushup: int
    rotary_stability: int

class WorkoutFromScoresRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    calculated_scores: CalculatedScores
    student_id: Optional[int] = None


class StudentIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    days_per_week: int = 3
    equipment: Optional[List[str]] = None
    injuries: Optional[str] = None
    lift_maxes: Optional[Dict[str, float]] = None
    lift_max_source: Optional[str] = "coach"


class CoachIn(BaseModel):
    name: Optional[str] = None


class ModulePatch(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class CoachAdminPatch(BaseModel):
    is_admin: bool


class AdminSessionIn(BaseModel):
    gate_secret: str


class ProgramFeedback(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_type: str
    payload: Dict[str, Any] = {}
    coach_plan: Optional[Dict[str, Any]] = None


def _dump(model: BaseModel) -> dict:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _student_out(student: Student) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "age": student.age,
        "gender": student.gender,
        "days_per_week": student.days_per_week,
        "equipment": student.equipment or [],
        "injuries": student.injuries,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "lift_maxes": {m.lift_key: m.one_rm for m in (student.lift_maxes or [])},
    }


LIFT_LOG_SOURCES = {"coach", "test", "estimated"}


def _normalize_lift_source(value: Optional[str]) -> str:
    key = str(value or "coach").strip().lower()
    return key if key in LIFT_LOG_SOURCES else "coach"


def _athlete_snapshot(student: Optional[Student], lift_maxes: dict) -> dict:
    if not student:
        return {
            "days_per_week": 3,
            "equipment": [],
            "lift_maxes": dict(lift_maxes or {}),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
    return {
        "days_per_week": student.days_per_week or 3,
        "equipment": list(student.equipment or []),
        "lift_maxes": {k: float(v) for k, v in (lift_maxes or {}).items() if v not in (None, "")},
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def _lift_changed(previous, nxt) -> bool:
    if previous is None:
        return True
    try:
        return abs(float(previous) - float(nxt)) > 1e-6
    except (TypeError, ValueError):
        return True


def _log_lift_max(db: AsyncSession, student_id: int, lift_key: str, one_rm: float, previous, source: str):
    db.add(
        LiftMaxLog(
            student_id=student_id,
            lift_key=lift_key,
            one_rm=float(one_rm),
            previous_one_rm=None if previous is None else float(previous),
            source=_normalize_lift_source(source),
        )
    )


def _program_out(program: ProgramDraft) -> dict:
    plan = program.coach_plan or program.ai_plan or {}
    return {
        "id": program.id,
        "assessment_id": program.assessment_id,
        "student_id": program.student_id,
        "status": program.status,
        "ai_plan": program.ai_plan,
        "coach_plan": program.coach_plan,
        "workout": plan,
        "candidate_exercises": program.candidate_exercises or plan.get("candidate_exercises") or {},
        "created_at": program.created_at.isoformat() if program.created_at else None,
        "approved_at": program.approved_at.isoformat() if program.approved_at else None,
        "block_id": program.block_id,
        "week_index": program.week_index or 1,
        **({} if not isinstance(plan, dict) else {k: v for k, v in plan.items() if k not in {"candidate_exercises"}}),
    }


async def _owned_student(student_id: int, coach: Coach, db: AsyncSession) -> Student:
    result = await db.execute(
        select(Student).where(Student.id == int(student_id), Student.coach_id == coach.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


async def _load_priors(coach_id: int, db: AsyncSession) -> dict:
    rows = (
        await db.execute(select(CoachExercisePrior).where(CoachExercisePrior.coach_id == coach_id))
    ).scalars().all()
    priors = {}
    for row in rows:
        priors[f"{row.exercise_id}|{row.context_key}"] = {
            "shown": row.shown,
            "kept": row.kept,
            "replaced": row.replaced,
        }
    return priors


async def _bump_prior(db: AsyncSession, coach_id: int, exercise_id: str, context_key: str, field: str):
    result = await db.execute(
        select(CoachExercisePrior).where(
            CoachExercisePrior.coach_id == coach_id,
            CoachExercisePrior.exercise_id == exercise_id,
            CoachExercisePrior.context_key == (context_key or ""),
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = CoachExercisePrior(
            coach_id=coach_id,
            exercise_id=exercise_id,
            context_key=context_key or "",
            shown=0,
            kept=0,
            replaced=0,
        )
        db.add(row)
    setattr(row, field, getattr(row, field) + 1)


def _iter_plan_items(plan: dict):
    skip_if_v2 = {"main", "backdown"}
    for day in plan.get("days") or []:
        blocks = day.get("blocks") or {}
        has_v2 = "block_a" in blocks or "block_b" in blocks
        for slot, items in blocks.items():
            if not isinstance(items, list):
                continue
            if has_v2 and slot in skip_if_v2:
                continue
            for item in items:
                if isinstance(item, dict):
                    yield slot, item


async def _process_program_generation(
    full_data: Dict[str, Any],
    db: AsyncSession,
    coach: Optional[Coach] = None,
    student: Optional[Student] = None,
):
    try:
        lift_maxes = {}
        days = 3
        if student:
            days = student.days_per_week or 3
            maxes = (
                await db.execute(select(LiftMax).where(LiftMax.student_id == student.id))
            ).scalars().all()
            lift_maxes = {m.lift_key: m.one_rm for m in maxes}
            full_data = {
                **full_data,
                "athlete_context": {
                    **(full_data.get("athlete_context") or {}),
                    "age": student.age,
                    "gender": student.gender,
                },
            }
        priors = await _load_priors(coach.id, db) if coach else {}
        plan = assemble_weekly_program(
            full_data,
            days_per_week=days,
            lift_maxes=lift_maxes,
            priors=priors,
            use_manual_scores=full_data.get("use_manual_scores", False),
            equipment=(student.equipment if student else None),
        )
        plan = enrich_coach_notes(plan, (plan.get("analysis") or {}).get("comments"))
        plan["athlete_snapshot"] = _athlete_snapshot(student, lift_maxes)
        analysis = plan.get("analysis") or analyze_assessment_session(
            full_data,
            athlete_context={
                "age": student.age if student else None,
                "gender": student.gender if student else None,
            },
        )
        scores = analysis.get("effective_scores", {})
        session = normalize_session(full_data)

        assessment = None
        program = None
        if student and coach:
            assessment = Assessment(
                student_id=student.id,
                assessment_kind=analysis.get("assessment_kind") or "baseline_session",
                selected_batteries=session.get("selected_batteries") or analysis.get("selected_batteries") or [],
                raw_json_data=full_data,
                scores=scores,
                comments=analysis.get("comments") or {},
                needs=analysis.get("needs") or [],
                findings=analysis.get("findings") or [],
                total_score=analysis.get("total_score", 0),
                status=analysis.get("status"),
            )
            db.add(assessment)
            await db.flush()
            tmpl = template_for(analysis.get("status") or "PATTERN", load_methodology())
            block = TrainingBlock(
                student_id=student.id,
                coach_id=coach.id,
                assessment_id=assessment.id,
                status="active" if analysis.get("status") != "STOP" else "referral",
                week_count=int(tmpl.get("weeks") or 1),
                current_week=1,
                methodology_version=str((load_methodology() or {}).get("schema_version") or 3),
            )
            db.add(block)
            await db.flush()
            plan["block_id"] = block.id
            plan["week_index"] = 1
            program = ProgramDraft(
                student_id=student.id,
                assessment_id=assessment.id,
                coach_id=coach.id,
                status="draft",
                ai_plan=plan,
                coach_plan=None,
                candidate_exercises=plan.get("candidate_exercises") or {},
                context_key=plan.get("context_key"),
                block_id=block.id,
                week_index=1,
            )
            db.add(program)
            for _, item in _iter_plan_items(plan):
                if item.get("exercise_id"):
                    await _bump_prior(
                        db, coach.id, item["exercise_id"], plan.get("context_key") or "", "shown"
                    )
            await db.commit()
            await db.refresh(program)
            plan["id"] = program.id
            plan["assessment_id"] = assessment.id
            plan["status"] = "draft"
            if firestore_enabled():
                mirror_coach(coach.firebase_uid, {"name": coach.name, "email": coach.email, "legacy_id": coach.id})
                mirror_athlete(coach.firebase_uid, str(student.id), {"name": student.name, "legacy_id": student.id})
                mirror_program(coach.firebase_uid, str(student.id), str(program.id), {"status": "draft", "week_index": 1})
        else:
            await db.commit()

        plan["calculated_scores"] = scores
        return _program_out(program) if program else plan
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Generation Error: {exc}")


@app.get("/me")
async def me(coach: Coach = Depends(get_current_coach)):
    return {
        "id": coach.id,
        "name": coach.name,
        "email": coach.email,
        "firebase_uid": coach.firebase_uid,
        "is_admin": bool(coach.is_admin),
    }


def _module_out(row: PlatformModule) -> dict:
    spec = CATALOG_BY_ID.get(row.module_id, {})
    return {
        "id": row.module_id,
        "name": spec.get("name", row.module_id),
        "description": spec.get("description", ""),
        "category": spec.get("category", "platform"),
        "scope": spec.get("scope", "coach"),
        "version": spec.get("version", "1.0.0"),
        "enabled": bool(row.enabled),
        "config": row.config or {},
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@app.get("/modules")
async def list_modules(coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(PlatformModule).order_by(PlatformModule.module_id.asc()))).scalars().all()
    modules = [_module_out(r) for r in rows]
    if coach.is_admin:
        return {"modules": modules, "is_admin": True}
    return {
        "modules": [m for m in modules if m["scope"] != "admin" and m["enabled"]],
        "is_admin": False,
    }


@app.post("/admin/session")
async def create_admin_session(payload: AdminSessionIn, coach: Coach = Depends(get_current_coach)):
    """Unlock admin panel: Firebase coach auth + ADMIN_GATE_SECRET + is_admin."""
    verify_admin_gate_secret(payload.gate_secret)
    if not coach.is_admin:
        raise HTTPException(status_code=403, detail="This account is not an admin")
    token, expires_at = mint_admin_session_token(coach.id)
    return {
        "admin_token": token,
        "expires_at": expires_at,
        "coach": {
            "id": coach.id,
            "name": coach.name,
            "email": coach.email,
            "is_admin": True,
        },
        "gate_configured": admin_gate_configured(),
    }


@app.get("/admin/overview")
async def admin_overview(admin: Coach = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    coaches = (await db.execute(select(func.count()).select_from(Coach))).scalar_one()
    students = (await db.execute(select(func.count()).select_from(Student))).scalar_one()
    assessments = (await db.execute(select(func.count()).select_from(Assessment))).scalar_one()
    programs = (await db.execute(select(func.count()).select_from(ProgramDraft))).scalar_one()
    blocks = (await db.execute(select(func.count()).select_from(TrainingBlock))).scalar_one()
    enabled_modules = (
        await db.execute(select(func.count()).select_from(PlatformModule).where(PlatformModule.enabled.is_(True)))
    ).scalar_one()
    groq = bool(os.getenv("GROQ_API_KEY"))
    return {
        "coaches": coaches,
        "students": students,
        "assessments": assessments,
        "programs": programs,
        "blocks": blocks,
        "enabled_modules": enabled_modules,
        "integrations": {
            "groq": groq,
            "firestore_mirror": firestore_enabled(),
            "database": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "local",
        },
    }


@app.get("/admin/coaches")
async def admin_coaches(admin: Coach = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Coach).order_by(Coach.created_at.desc()))).scalars().all()
    out = []
    for coach in rows:
        student_count = (
            await db.execute(select(func.count()).select_from(Student).where(Student.coach_id == coach.id))
        ).scalar_one()
        out.append(
            {
                "id": coach.id,
                "name": coach.name,
                "email": coach.email,
                "is_admin": bool(coach.is_admin),
                "student_count": student_count,
                "created_at": coach.created_at.isoformat() if coach.created_at else None,
            }
        )
    return out


@app.patch("/admin/coaches/{coach_id}")
async def admin_patch_coach(
    coach_id: int,
    payload: CoachAdminPatch,
    admin: Coach = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(select(Coach).where(Coach.id == coach_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Coach not found")
    if row.id == admin.id and not payload.is_admin:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin access")
    row.is_admin = payload.is_admin
    await db.commit()
    await db.refresh(row)
    return {"id": row.id, "is_admin": bool(row.is_admin)}


@app.patch("/admin/modules/{module_id}")
async def admin_patch_module(
    module_id: str,
    payload: ModulePatch,
    admin: Coach = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if module_id not in CATALOG_BY_ID:
        raise HTTPException(status_code=404, detail="Unknown module")
    row = (
        await db.execute(select(PlatformModule).where(PlatformModule.module_id == module_id))
    ).scalar_one_or_none()
    if not row:
        spec = CATALOG_BY_ID[module_id]
        row = PlatformModule(
            module_id=module_id,
            enabled=bool(spec.get("default_enabled", True)),
            config={},
        )
        db.add(row)
        await db.flush()
    if payload.enabled is not None:
        row.enabled = payload.enabled
    if payload.config is not None:
        row.config = payload.config
    await db.commit()
    await db.refresh(row)
    return _module_out(row)


@app.get("/me/insights")
@app.get("/insights")
async def my_insights(coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    priors = await _load_priors(coach.id, db)
    return insights_payload(priors)


@app.post("/coaches")
async def register_coach(payload: CoachIn, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    if payload.name:
        coach.name = payload.name
        await db.commit()
        await db.refresh(coach)
    return {"id": coach.id, "name": coach.name}


@app.get("/students")
async def list_students(coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student).options(selectinload(Student.lift_maxes)).where(Student.coach_id == coach.id)
    )
    return [_student_out(s) for s in result.scalars().unique().all()]


@app.post("/students")
async def create_student(payload: StudentIn, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    if not payload.name:
        raise HTTPException(status_code=400, detail="Name required")
    student = Student(
        coach_id=coach.id,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        days_per_week=payload.days_per_week or 3,
        equipment=payload.equipment or [],
        injuries=payload.injuries,
    )
    db.add(student)
    await db.flush()
    for lift_key, one_rm in (payload.lift_maxes or {}).items():
        db.add(LiftMax(student_id=student.id, lift_key=lift_key, one_rm=float(one_rm)))
        _log_lift_max(db, student.id, lift_key, float(one_rm), None, payload.lift_max_source or "coach")
    await db.commit()
    result = await db.execute(
        select(Student).options(selectinload(Student.lift_maxes)).where(Student.id == student.id)
    )
    return _student_out(result.scalar_one())


@app.get("/students/{student_id}")
async def get_student(student_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    student = await _owned_student(student_id, coach, db)
    result = await db.execute(
        select(Student).options(selectinload(Student.lift_maxes)).where(Student.id == student.id)
    )
    return _student_out(result.scalar_one())


@app.patch("/students/{student_id}")
async def patch_student(student_id: int, payload: StudentIn, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    student = await _owned_student(student_id, coach, db)
    student.name = payload.name or student.name
    student.age = payload.age if payload.age is not None else student.age
    student.gender = payload.gender or student.gender
    student.days_per_week = payload.days_per_week or student.days_per_week
    student.equipment = payload.equipment if payload.equipment is not None else student.equipment
    student.injuries = payload.injuries if payload.injuries is not None else student.injuries
    if payload.lift_maxes:
        existing = (await db.execute(select(LiftMax).where(LiftMax.student_id == student.id))).scalars().all()
        by_key = {m.lift_key: m for m in existing}
        source = payload.lift_max_source or "coach"
        for lift_key, one_rm in payload.lift_maxes.items():
            nxt = float(one_rm)
            if lift_key in by_key:
                previous = by_key[lift_key].one_rm
                if _lift_changed(previous, nxt):
                    by_key[lift_key].one_rm = nxt
                    _log_lift_max(db, student.id, lift_key, nxt, previous, source)
            else:
                db.add(LiftMax(student_id=student.id, lift_key=lift_key, one_rm=nxt))
                _log_lift_max(db, student.id, lift_key, nxt, None, source)
    await db.commit()
    result = await db.execute(
        select(Student).options(selectinload(Student.lift_maxes)).where(Student.id == student.id)
    )
    return _student_out(result.scalar_one())


@app.get("/students/{student_id}/lift-maxes/history")
async def lift_max_history(student_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    student = await _owned_student(student_id, coach, db)
    current_rows = (
        await db.execute(select(LiftMax).where(LiftMax.student_id == student.id))
    ).scalars().all()
    logs = (
        await db.execute(
            select(LiftMaxLog)
            .where(LiftMaxLog.student_id == student.id)
            .order_by(LiftMaxLog.recorded_at.desc(), LiftMaxLog.id.desc())
        )
    ).scalars().all()
    history = [
            {
                "id": row.id,
                "lift_key": row.lift_key,
                "one_rm": row.one_rm,
                "previous_one_rm": row.previous_one_rm,
                "source": row.source or "coach",
                "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
            }
            for row in logs
        ]
    logged_keys = {row.lift_key for row in logs}
    for row in current_rows:
        if row.lift_key in logged_keys:
            continue
        history.append(
            {
                "id": None,
                "lift_key": row.lift_key,
                "one_rm": row.one_rm,
                "previous_one_rm": None,
                "source": "coach",
                "recorded_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        )
    history.sort(key=lambda item: item.get("recorded_at") or "", reverse=True)
    return {
        "current": {
            row.lift_key: {
                "one_rm": row.one_rm,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
            for row in current_rows
        },
        "history": history,
    }


@app.get("/students/{student_id}/assessments")
async def list_assessments(student_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    await _owned_student(student_id, coach, db)
    rows = (
        await db.execute(
            select(Assessment).where(Assessment.student_id == student_id).order_by(Assessment.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": a.id,
            "student_id": a.student_id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "scores": a.scores,
            "comments": a.comments,
            "needs": a.needs,
            "findings": a.findings,
            "selected_batteries": a.selected_batteries,
            "assessment_kind": a.assessment_kind,
            "total_score": a.total_score,
            "status": a.status,
        }
        for a in rows
    ]


@app.post("/students/{student_id}/assessments")
async def save_assessment(student_id: int, payload: Dict[str, Any], coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    student = await _owned_student(student_id, coach, db)
    profile = payload.get("raw_fms_inputs") or payload
    analysis = analyze_assessment_session(
        profile,
        use_manual_scores=profile.get("use_manual_scores", False),
        athlete_context={"age": student.age, "gender": student.gender},
    )
    session = normalize_session(profile)
    row = Assessment(
        student_id=int(student_id),
        assessment_kind=analysis.get("assessment_kind") or "baseline_session",
        selected_batteries=session.get("selected_batteries") or [],
        raw_json_data=profile,
        scores=payload.get("calculated_scores") or analysis.get("effective_scores"),
        comments=analysis.get("comments") or {},
        needs=analysis.get("needs") or [],
        findings=analysis.get("findings") or [],
        total_score=analysis.get("total_score", 0),
        status=analysis.get("status"),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {
        "id": row.id,
        "assessment_id": row.id,
        "scores": row.scores,
        "status": row.status,
        "findings": row.findings,
        "selected_batteries": row.selected_batteries,
        "battery_results": analysis.get("battery_results"),
    }


@app.get("/assessment/batteries")
async def list_assessment_batteries(coach: Coach = Depends(get_current_coach)):
    return load_registry()


@app.post("/tools/estimate-1rm")
async def tools_estimate_1rm(body: LoadEstimateRequest, coach: Coach = Depends(get_current_coach)):
    estimated = estimate_1rm(body.load_kg, body.reps, body.rpe)
    out = {**estimated, "rm_ladder": rm_ladder_loads(estimated["estimated_1rm"])}
    if body.include_pro_rata:
        out["pro_rata"] = pro_rata_maxes(estimated["estimated_1rm"], body.anchor_lift or "back_squat")
    return out


@app.get("/tools/load-tables")
async def tools_load_tables(coach: Coach = Depends(get_current_coach)):
    return load_tables()



@app.get("/students/{student_id}/workouts")
async def list_workouts(
    student_id: int,
    status: Optional[str] = Query(default="all"),
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    query = select(ProgramDraft).where(ProgramDraft.student_id == student_id)
    if status and status != "all":
        query = query.where(ProgramDraft.status == status)
    rows = (await db.execute(query.order_by(ProgramDraft.created_at.desc()))).scalars().all()
    return [_program_out(p) for p in rows]


@app.post("/students/{student_id}/workouts")
async def save_workout(student_id: int, payload: Dict[str, Any], coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    await _owned_student(student_id, coach, db)
    program = ProgramDraft(
        student_id=int(student_id),
        assessment_id=payload.get("assessment_id"),
        coach_id=coach.id,
        status=payload.get("status") or "draft",
        ai_plan=payload.get("ai_plan") or payload,
        coach_plan=payload.get("coach_plan"),
        candidate_exercises=payload.get("candidate_exercises") or {},
        context_key=payload.get("context_key"),
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return _program_out(program)


@app.get("/students/{student_id}/workouts/{program_id}")
async def get_workout(student_id: int, program_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    await _owned_student(student_id, coach, db)
    program = (
        await db.execute(
            select(ProgramDraft).where(
                ProgramDraft.id == program_id, ProgramDraft.student_id == int(student_id)
            )
        )
    ).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return _program_out(program)


@app.patch("/students/{student_id}/workouts/{program_id}")
async def patch_workout(
    student_id: int,
    program_id: int,
    payload: ProgramFeedback,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    program = (
        await db.execute(
            select(ProgramDraft).where(
                ProgramDraft.id == program_id, ProgramDraft.student_id == int(student_id)
            )
        )
    ).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    if program.snapshot_immutable and payload.event_type in {"replace_exercise", "approve_as_is", "reject_session"}:
        raise HTTPException(status_code=409, detail="Approved week is immutable")

    event_id = (payload.payload or {}).get("event_id") or str(uuid.uuid4())
    existing = (
        await db.execute(select(PreferenceEvent).where(PreferenceEvent.event_id == event_id))
    ).scalar_one_or_none()
    if existing:
        return _program_out(program)

    event_type = payload.event_type
    if event_type == "approve_as_is" and plans_differ_selection(program.ai_plan, payload.coach_plan or program.coach_plan):
        event_type = "approve_edited"

    event = PreferenceEvent(
        coach_id=coach.id,
        program_id=program.id,
        event_type=event_type,
        payload=payload.payload or {},
        context_key=program.context_key,
        event_id=event_id,
        reason_code=(payload.payload or {}).get("reason_code"),
    )
    db.add(event)

    if payload.coach_plan is not None:
        program.coach_plan = payload.coach_plan

    if event_type == "replace_exercise":
        out_id = payload.payload.get("out_id")
        in_id = payload.payload.get("in_id")
        if out_id:
            await _bump_prior(db, coach.id, out_id, program.context_key or "", "replaced")
        if in_id:
            await _bump_prior(db, coach.id, in_id, program.context_key or "", "kept")
            catalog = catalog_by_id()
            plan = program.coach_plan or json.loads(json.dumps(program.ai_plan))
            slot = payload.payload.get("slot")
            for day in plan.get("days") or []:
                items = (day.get("blocks") or {}).get(slot) or []
                for i, item in enumerate(items):
                    if item.get("exercise_id") == out_id and in_id in catalog:
                        replacement = dict(item)
                        replacement["exercise_id"] = in_id
                        replacement["name"] = catalog[in_id]["name"]
                        replacement["unfilled"] = False
                        items[i] = replacement
            program.coach_plan = plan
    elif event_type == "approve_as_is":
        program.status = "approved"
        program.approved_at = datetime.now(timezone.utc)
        program.snapshot_immutable = True
        plan = program.coach_plan or program.ai_plan or {}
        for _, item in _iter_plan_items(plan):
            if item.get("exercise_id"):
                await _bump_prior(db, coach.id, item["exercise_id"], program.context_key or "", "kept")
    elif event_type == "approve_edited":
        program.status = "approved"
        program.approved_at = datetime.now(timezone.utc)
        program.snapshot_immutable = True
    elif event_type == "reject_session":
        program.status = "rejected"
    elif event_type == "edit_prescription" and payload.coach_plan is not None:
        program.coach_plan = payload.coach_plan

    await db.commit()
    await db.refresh(program)
    if firestore_enabled():
        mirror_program(coach.firebase_uid, str(student_id), str(program.id), {"status": program.status})
    return _program_out(program)


@app.post("/generate-workout")
@app.post("/generate-program")
async def generate_workout(
    profile: AssessmentSessionRequest,
    db: AsyncSession = Depends(get_db),
    coach: Coach = Depends(get_current_coach),
):
    full_data = _dump(profile)
    student = None
    student_id = full_data.get("student_id")
    if student_id:
        student = await _owned_student(int(student_id), coach, db)
        full_data.setdefault(
            "athlete_context",
            {"age": student.age, "gender": student.gender},
        )
    return await _process_program_generation(full_data, db, coach, student)


@app.post("/generate-workout-from-scores")
async def generate_workout_from_scores(
    request: WorkoutFromScoresRequest,
    db: AsyncSession = Depends(get_db),
    coach: Coach = Depends(get_current_coach),
):
    score_dict = _dump(request.calculated_scores)
    for k, v in score_dict.items():
        if v is None or not (0 <= v <= 3):
            raise HTTPException(status_code=400, detail=f"Score for {k} must be between 0 and 3.")
    dummy_profile = {name: {"score": value} for name, value in score_dict.items()}
    dummy_profile["use_manual_scores"] = True
    student = None
    if request.student_id:
        student = await _owned_student(int(request.student_id), coach, db)
    return await _process_program_generation(dummy_profile, db, coach, student)


def _active_plan(program: ProgramDraft) -> dict:
    return program.coach_plan or program.ai_plan or {}


@app.get("/students/{student_id}/blocks")
async def list_blocks(student_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    await _owned_student(student_id, coach, db)
    rows = (
        await db.execute(
            select(TrainingBlock).where(TrainingBlock.student_id == student_id).order_by(TrainingBlock.created_at.desc())
        )
    ).scalars().all()
    return [
        {
            "id": b.id,
            "student_id": b.student_id,
            "assessment_id": b.assessment_id,
            "status": b.status,
            "week_count": b.week_count,
            "current_week": b.current_week,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in rows
    ]


@app.get("/students/{student_id}/blocks/{block_id}")
async def get_block(student_id: int, block_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    await _owned_student(student_id, coach, db)
    block = (
        await db.execute(
            select(TrainingBlock).where(TrainingBlock.id == block_id, TrainingBlock.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    weeks = (
        await db.execute(
            select(ProgramDraft)
            .where(ProgramDraft.block_id == block.id)
            .order_by(ProgramDraft.week_index.asc())
        )
    ).scalars().all()
    return {
        "id": block.id,
        "status": block.status,
        "week_count": block.week_count,
        "current_week": block.current_week,
        "weeks": [_program_out(w) for w in weeks],
        "retest_due": block.current_week >= block.week_count,
    }


async def _materialize_week(student_id: int, block: TrainingBlock, week_index: int, coach: Coach, db: AsyncSession) -> ProgramDraft:
    existing = (
        await db.execute(
            select(ProgramDraft).where(ProgramDraft.block_id == block.id, ProgramDraft.week_index == week_index)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    if week_index < 1 or week_index > block.week_count:
        raise HTTPException(status_code=400, detail="Week out of range")
    week1 = (
        await db.execute(
            select(ProgramDraft).where(ProgramDraft.block_id == block.id, ProgramDraft.week_index == 1)
        )
    ).scalar_one_or_none()
    if not week1:
        raise HTTPException(status_code=404, detail="Week 1 not found")
    source = week1.coach_plan or week1.ai_plan or {}
    plan = apply_week_progression(source, week_index, load_methodology())
    plan["block_id"] = block.id
    row = ProgramDraft(
        student_id=student_id,
        assessment_id=block.assessment_id,
        coach_id=coach.id,
        status="draft",
        ai_plan=plan,
        coach_plan=None,
        candidate_exercises=plan.get("candidate_exercises") or week1.candidate_exercises or {},
        context_key=week1.context_key,
        block_id=block.id,
        week_index=week_index,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@app.get("/students/{student_id}/blocks/{block_id}/weeks/{week_index}")
async def get_block_week(
    student_id: int,
    block_id: int,
    week_index: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    block = (
        await db.execute(
            select(TrainingBlock).where(TrainingBlock.id == block_id, TrainingBlock.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    row = await _materialize_week(student_id, block, week_index, coach, db)
    return _program_out(row)


@app.post("/students/{student_id}/blocks/{block_id}/advance")
async def advance_block(
    student_id: int,
    block_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    block = (
        await db.execute(
            select(TrainingBlock).where(TrainingBlock.id == block_id, TrainingBlock.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    nxt = min(block.week_count, (block.current_week or 1) + 1)
    block.current_week = nxt
    row = await _materialize_week(student_id, block, nxt, coach, db)
    return {"block_id": block.id, "current_week": block.current_week, "program": _program_out(row)}


@app.post("/students/{student_id}/blocks/{block_id}/retest")
async def mark_retest(
    student_id: int,
    block_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    block = (
        await db.execute(
            select(TrainingBlock).where(TrainingBlock.id == block_id, TrainingBlock.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    block.status = "retest_due"
    await db.commit()
    return {"block_id": block.id, "status": block.status, "retest_due": True}


@app.get("/students/{student_id}/insights")
async def student_insights(student_id: int, coach: Coach = Depends(get_current_coach), db: AsyncSession = Depends(get_db)):
    await _owned_student(student_id, coach, db)
    priors = await _load_priors(coach.id, db)
    return insights_payload(priors)


@app.post("/students/{student_id}/workouts/{program_id}/share")
async def create_share(
    student_id: int,
    program_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    program = (
        await db.execute(
            select(ProgramDraft).where(ProgramDraft.id == program_id, ProgramDraft.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    if program.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved programs can be shared")
    raw = mint_share_token()
    row = ShareLink(
        program_id=program.id,
        student_id=student_id,
        coach_id=coach.id,
        token_hash=hash_token(raw),
        expires_at=default_expiry(),
    )
    db.add(row)
    await db.commit()
    return {"token": raw, "expires_at": row.expires_at.isoformat(), "url_path": f"/v/{raw}"}


@app.post("/students/{student_id}/workouts/{program_id}/share/revoke")
async def revoke_share(
    student_id: int,
    program_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    rows = (
        await db.execute(select(ShareLink).where(ShareLink.program_id == program_id, ShareLink.revoked_at.is_(None)))
    ).scalars().all()
    now = datetime.now(timezone.utc)
    for row in rows:
        row.revoked_at = now
    await db.commit()
    return {"revoked": len(rows)}


@app.get("/public/programs/{token}")
async def public_program(token: str, db: AsyncSession = Depends(get_db)):
    hashed = hash_token(token)
    link = (await db.execute(select(ShareLink).where(ShareLink.token_hash == hashed))).scalar_one_or_none()
    if not link or link.revoked_at:
        raise HTTPException(status_code=404, detail="Share not found")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share expired")
    program = (await db.execute(select(ProgramDraft).where(ProgramDraft.id == link.program_id))).scalar_one_or_none()
    if not program or program.status != "approved":
        raise HTTPException(status_code=404, detail="Program not found")
    return athlete_dto(_active_plan(program))


@app.get("/students/{student_id}/workouts/{program_id}/export.xlsx")
async def export_xlsx(
    student_id: int,
    program_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    program = (
        await db.execute(
            select(ProgramDraft).where(ProgramDraft.id == program_id, ProgramDraft.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    data = plan_to_xlsx_bytes(_active_plan(program))
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="fitai-week-{program_id}.xlsx"'},
    )


@app.get("/students/{student_id}/workouts/{program_id}/export.pdf")
async def export_pdf(
    student_id: int,
    program_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    program = (
        await db.execute(
            select(ProgramDraft).where(ProgramDraft.id == program_id, ProgramDraft.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    plan = _active_plan(program)
    pdf = plan_to_pdf_bytes(plan)
    if pdf:
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="fitai-week-{program_id}.pdf"'},
        )
    return HTMLResponse(plan_to_html(plan))


@app.get("/students/{student_id}/workouts/{program_id}/print")
async def print_program(
    student_id: int,
    program_id: int,
    coach: Coach = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    await _owned_student(student_id, coach, db)
    program = (
        await db.execute(
            select(ProgramDraft).where(ProgramDraft.id == program_id, ProgramDraft.student_id == student_id)
        )
    ).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return HTMLResponse(plan_to_html(_active_plan(program)))


@app.get("/public/programs/{token}/print")
async def public_print(token: str, db: AsyncSession = Depends(get_db)):
    hashed = hash_token(token)
    link = (await db.execute(select(ShareLink).where(ShareLink.token_hash == hashed))).scalar_one_or_none()
    if not link or link.revoked_at:
        raise HTTPException(status_code=404, detail="Share not found")
    program = (await db.execute(select(ProgramDraft).where(ProgramDraft.id == link.program_id))).scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return HTMLResponse(plan_to_html(athlete_dto(_active_plan(program)), athlete=True))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

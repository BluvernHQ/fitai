import json
import hashlib
import uvicorn
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# ── IMPORTS ──
# Ensure these files exist in your src folder
from src.logic.fms_analyzer import analyze_fms_profile
from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan
from src.database import init_db, AsyncSessionLocal, AssessmentLog

# ────────────────────────────────────────────────
# Lifecycle (Startup)
# ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up: Connecting to NeonDB...")
    await init_db()  # Create tables if they don't exist
    print("✅ Neon DB Connection Verified.")
    yield

app = FastAPI(title="FMS Smart Coach API", version="3.3", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESPONSE_CACHE = {}

# ────────────────────────────────────────────────
# Pydantic Models (Updated for L/R & Database)
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
    score: int
    trunk_torso: OS_TrunkTorso
    lower_limb: OS_LowerLimb
    feet: OS_Feet
    upper_body_bar_position: OS_UpperBodyBarPosition

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
    score: int
    l_score: int = 0  # Added for DB
    r_score: int = 0  # Added for DB
    pelvis_core_control: HS_PelvisCoreControl
    stance_leg: HS_StanceLeg
    stepping_leg: HS_SteppingLeg

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
    score: int
    l_score: int = 0
    r_score: int = 0
    alignment: IL_Alignment
    lower_body_control: IL_LowerBodyControl
    balance_stability: IL_BalanceStability

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
    score: int
    l_score: int = 0
    r_score: int = 0
    clearing_pain: bool = False # Added for DB
    reach_quality: SM_ReachQuality
    compensation: SM_Compensation
    pain: SM_Pain

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
    score: int
    l_score: int = 0
    r_score: int = 0
    non_moving_leg: ASLR_NonMovingLeg
    moving_leg: ASLR_MovingLeg
    pelvic_control: ASLR_PelvicControl

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
    score: int
    clearing_pain: bool = False
    body_alignment: TSP_BodyAlignment
    core_control: TSP_CoreControl
    upper_body: TSP_UpperBody

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
    score: int
    l_score: int = 0
    r_score: int = 0
    clearing_pain: bool = False
    diagonal_pattern: RS_DiagonalPattern
    spinal_control: RS_SpinalControl
    symmetry: RS_Symmetry

class FMSProfileRequest(BaseModel):
    overhead_squat: OverheadSquatData
    hurdle_step: HurdleStepData
    inline_lunge: InlineLungeData
    shoulder_mobility: ShoulderMobilityData
    active_straight_leg_raise: ASLRData
    trunk_stability_pushup: TSPData
    rotary_stability: RSData
    use_manual_scores: bool = False

# ────────────────────────────────────────────────
# API Endpoints
# ────────────────────────────────────────────────

@app.post("/generate-workout")
async def generate_workout(profile: FMSProfileRequest):
    # Convert Pydantic model to dictionary
    full_data = profile.dict()

    # Create simplified scores for the RAG engine
    simple_scores = {
        "overhead_squat": full_data["overhead_squat"]["score"],
        "hurdle_step": full_data["hurdle_step"]["score"],
        "inline_lunge": full_data["inline_lunge"]["score"],
        "shoulder_mobility": full_data["shoulder_mobility"]["score"],
        "active_straight_leg_raise": full_data["active_straight_leg_raise"]["score"],
        "trunk_stability_pushup": full_data["trunk_stability_pushup"]["score"],
        "rotary_stability": full_data["rotary_stability"]["score"],
    }

    # 1. ANALYZE
    try:
        # We pass the full nested data to the analyzer
        analysis = analyze_fms_profile(full_data, use_manual_scores=full_data.get('use_manual_scores', False))
    except Exception as e:
        print(f"Analyzer Error: {e}")
        raise HTTPException(status_code=500, detail=f"Analyzer Error: {str(e)}")

    if analysis.get("status") == "STOP":
        return {
            "session_title": "Medical Referral Required",
            "coach_summary": analysis.get("reason", "Pain detected."),
            "exercises": [],
            "difficulty_color": "Red"
        }

    # 2. RETRIEVE (RAG)
    try:
        retrieval_result = await get_exercises_by_profile(
            simple_scores=simple_scores,
            detailed_faults=full_data # Pass full details for better filtering
        )
        exercises = retrieval_result["data"]
    except Exception as e:
        print(f"Retriever Error: {e}")
        raise HTTPException(status_code=500, detail=f"Retriever Error: {str(e)}")

    # 3. GENERATE PLAN
    try:
        enriched_analysis = analysis.copy()
        enriched_analysis["detailed_faults"] = full_data
        
        final_plan = generate_workout_plan(enriched_analysis, exercises)
        
        level = analysis.get("target_level", 1)
        if final_plan.get("difficulty_color") != "Red":
            final_plan["difficulty_color"] = "Red" if level <= 3 else "Yellow" if level <= 6 else "Green"

        final_plan["effective_scores"] = analysis.get("effective_scores", {})

        # ── 4. SAVE TO NEON DATABASE ──
        if full_data: 
            async with AsyncSessionLocal() as session:
                new_result = AssessmentLog(
                    # --- 1. Deep Squat ---
                    deep_squat_score = profile.overhead_squat.score,
                    deep_squat_details = full_data["overhead_squat"], # Saves nested JSON faults

                    # --- 2. Hurdle Step ---
                    hurdle_step_l = profile.hurdle_step.l_score,
                    hurdle_step_r = profile.hurdle_step.r_score,
                    hurdle_step_final = profile.hurdle_step.score,
                    hurdle_step_details = full_data["hurdle_step"],

                    # --- 3. Inline Lunge ---
                    inline_lunge_l = profile.inline_lunge.l_score,
                    inline_lunge_r = profile.inline_lunge.r_score,
                    inline_lunge_final = profile.inline_lunge.score,
                    inline_lunge_details = full_data["inline_lunge"],

                    # --- 4. Shoulder Mobility ---
                    shoulder_mobility_l = profile.shoulder_mobility.l_score,
                    shoulder_mobility_r = profile.shoulder_mobility.r_score,
                    shoulder_clearing_pain = profile.shoulder_mobility.clearing_pain,
                    shoulder_mobility_final = profile.shoulder_mobility.score,
                    shoulder_mobility_details = full_data["shoulder_mobility"],

                    # --- 5. ASLR ---
                    aslr_l = profile.active_straight_leg_raise.l_score,
                    aslr_r = profile.active_straight_leg_raise.r_score,
                    aslr_final = profile.active_straight_leg_raise.score,
                    aslr_details = full_data["active_straight_leg_raise"],

                    # --- 6. Trunk Stability ---
                    trunk_stability_raw = profile.trunk_stability_pushup.score, # Raw score
                    extension_clearing_pain = profile.trunk_stability_pushup.clearing_pain,
                    trunk_stability_final = profile.trunk_stability_pushup.score,
                    trunk_stability_details = full_data["trunk_stability_pushup"],

                    # --- 7. Rotary Stability ---
                    rotary_stability_l = profile.rotary_stability.l_score,
                    rotary_stability_r = profile.rotary_stability.r_score,
                    flexion_clearing_pain = profile.rotary_stability.clearing_pain,
                    rotary_stability_final = profile.rotary_stability.score,
                    rotary_stability_details = full_data["rotary_stability"],

                    # --- Outputs ---
                    total_fms_score = final_plan.get("effective_scores", {}).get("total_score", 0),
                    predicted_level = "Calculated", 
                    analysis_summary = json.dumps(analysis), # Store as string
                    final_plan_json = str(final_plan)
                )
                
                session.add(new_result)
                await session.commit()
                print(f"DEBUG: Saved FMS result to Neon DB.")

        return final_plan

    except Exception as e:
        print(f"System Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System Error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from typing import Optional

# Import your modules
from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan

app = FastAPI(
    title="FMS Smart Coach API",
    description="7-Point FMS Logic Engine that generates personalized workout cards.",
    version="2.0"
)

# --- 1. DEFINE THE INPUT MODEL (The 7 Scores) ---
class FMSProfileRequest(BaseModel):
    deep_squat: int = Field(..., ge=0, le=3, description="Score for Deep Squat")
    hurdle_step: int = Field(..., ge=0, le=3, description="Score for Hurdle Step")
    inline_lunge: int = Field(..., ge=0, le=3, description="Score for Inline Lunge")
    shoulder_mobility: int = Field(..., ge=0, le=3, description="Score for Shoulder Mobility")
    active_straight_leg_raise: int = Field(..., ge=0, le=3, description="Score for ASLR")
    trunk_stability_pushup: int = Field(..., ge=0, le=3, description="Score for Trunk Stability")
    rotary_stability: int = Field(..., ge=0, le=3, description="Score for Rotary Stability")
    pain_present: bool = Field(False, description="Is there pain during any test?")

# --- 2. DEFINE THE ENDPOINT ---
@app.post("/generate-workout", summary="Generate Coach Plan from 7 Scores")
async def generate_workout(profile: FMSProfileRequest):
    """
    Analyzes the full FMS profile and returns a structured workout plan.
    """
    
    # Convert Pydantic model to simple dict
    scores = profile.dict()
    
    # 1. SAFETY CHECK (Pain Override)
    if scores['pain_present']:
        return {
            "session_title": "Medical Referral Required",
            "difficulty_color": "Red",
            "coach_summary": "Pain reported during screening. Training is contraindicated.",
            "exercises": []
        }

    # 2. RUN THE RETRIEVER (Analyzer + Data Fetch)
    try:
        retrieval_result = get_exercises_by_profile(scores)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retriever Error: {str(e)}")

    # Handle "STOP" cases (e.g., Score 0 detected by logic)
    if retrieval_result['status'] == "STOP":
        return {
            "session_title": "Medical Referral Required",
            "difficulty_color": "Red",
            "coach_summary": retrieval_result['message'],
            "exercises": []
        }

    # 3. RUN THE GENERATOR (AI Formatting)
    try:
        analysis = retrieval_result['analysis']
        exercises = retrieval_result['data']
        
        final_plan = generate_workout_plan(analysis, exercises)
        return final_plan

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generator Error: {str(e)}")

# --- 3. RUNNER ---
if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
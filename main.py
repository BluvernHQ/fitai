import json
import hashlib
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from typing import Optional, List

# --- DeepEval Imports ---
from deepeval.test_case import LLMTestCase
from deepeval import evaluate
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
try:
    from groq_judge import GroqJudge
except ImportError:
    print("⚠️ Warning: groq_judge.py not found. Evaluation will be skipped.")
    GroqJudge = None

# --- Import your modules ---
from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan

app = FastAPI(
    title="FMS Smart Coach API",
    description="7-Point FMS Logic Engine that generates personalized workout cards with Live Evaluation.",
    version="2.3"
)

# --- 1. CRITICAL FOR FRONTEND: ALLOW CROSS-ORIGIN REQUESTS (CORS) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all frontend apps to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. GLOBAL CACHE (The "Consistency" Fix) ---
# This dictionary stores previous results so we don't re-roll the dice.
RESPONSE_CACHE = {}

# --- 3. DEFINE THE INPUT MODEL ---
class FMSProfileRequest(BaseModel):
    deep_squat: int = Field(..., ge=0, le=3, description="Score for Deep Squat")
    hurdle_step: int = Field(..., ge=0, le=3, description="Score for Hurdle Step")
    inline_lunge: int = Field(..., ge=0, le=3, description="Score for Inline Lunge")
    shoulder_mobility: int = Field(..., ge=0, le=3, description="Score for Shoulder Mobility")
    active_straight_leg_raise: int = Field(..., ge=0, le=3, description="Score for ASLR")
    trunk_stability_pushup: int = Field(..., ge=0, le=3, description="Score for Trunk Stability")
    rotary_stability: int = Field(..., ge=0, le=3, description="Score for Rotary Stability")

# --- 4. BACKGROUND EVALUATION TASK ---
def run_deepeval_background(scores: dict, actual_output: str, retrieval_context: List[str]):
    if not GroqJudge:
        return
    print(f"⚖️ [Background] Starting Evaluation for user input...")
    try:
        groq_evaluator = GroqJudge(model="llama-3.3-70b-versatile")
        test_case = LLMTestCase(input=str(scores), actual_output=actual_output, retrieval_context=retrieval_context)
        faithfulness = FaithfulnessMetric(threshold=0.7, model=groq_evaluator, include_reason=False)
        relevancy = AnswerRelevancyMetric(threshold=0.7, model=groq_evaluator, include_reason=False)
        evaluate([test_case], metrics=[faithfulness, relevancy], print_results=False)
        print("✅ [Background] Evaluation Complete & Logged.")
    except Exception as e:
        print(f"❌ [Background] Evaluation Failed: {str(e)}")

# --- 5. DEFINE THE ENDPOINT ---
@app.post("/generate-workout", summary="Generate Coach Plan from 7 Scores")
async def generate_workout(profile: FMSProfileRequest, background_tasks: BackgroundTasks):
    """
    Analyzes the full FMS profile, returns a plan, and evaluates it in the background.
    """
    
    # Convert Pydantic model to simple dict
    scores = profile.dict()
    scores['pain_present'] = False

    # --- CACHE LOGIC: CHECK MEMORY FIRST ---
    # Create a unique ID for these specific scores
    cache_key = hashlib.md5(json.dumps(scores, sort_keys=True).encode()).hexdigest()

    if cache_key in RESPONSE_CACHE:
        print(f"⚡ CACHE HIT: Returning saved plan for consistent results.")
        return RESPONSE_CACHE[cache_key]

    # 1. RUN THE RETRIEVER
    try:
        retrieval_result = get_exercises_by_profile(scores)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retriever Error: {str(e)}")

    if retrieval_result['status'] == "STOP":
        return {
            "session_title": "Medical Referral Required",
            "difficulty_color": "Red",
            "coach_summary": retrieval_result['message'],
            "exercises": []
        }

    # 2. RUN THE GENERATOR
    try:
        analysis = retrieval_result['analysis']
        exercises = retrieval_result['data']
        final_plan = generate_workout_plan(analysis, exercises)

        # --- SAVE TO CACHE (So next time it's identical) ---
        RESPONSE_CACHE[cache_key] = final_plan

        # 3. BACKGROUND EVAL
        context_list = [f"{ex['exercise_name']}: {ex['description']}" for ex in exercises]
        actual_output_text = f"Title: {final_plan['session_title']}\nSummary: {final_plan['coach_summary']}"
        background_tasks.add_task(run_deepeval_background, scores=scores, actual_output=actual_output_text, retrieval_context=context_list)

        return final_plan

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generator Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
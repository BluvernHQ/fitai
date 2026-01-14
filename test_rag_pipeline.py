import pytest
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import time

# DeepEval Imports
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

# Import your Custom Judge
from groq_judge import GroqJudge

# Import your RAG Logic
try:
    from src.rag.retriever import get_exercises_by_profile
    from src.rag.generator import generate_workout_plan
except ImportError:
    print("❌ ERROR: Could not find 'src' folder. Run this from your project root.")
    exit()

# 1. Setup
load_dotenv()
# Force API Key from env if login command failed previously
# os.environ["CONFIDENT_API_KEY"] = "YOUR_KEY_HERE" 

groq_evaluator = GroqJudge(model="llama-3.3-70b-versatile")

# 2. Connect to Database (Updated with OFFSET)
def get_db_logs(limit=5, offset=0):
    db_url = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # We add OFFSET to skip previous batches
        query = text("SELECT * FROM assessment_logs ORDER BY timestamp DESC LIMIT :limit OFFSET :offset")
        result = conn.execute(query, {"limit": limit, "offset": offset})
        return result.fetchall()

# 3. The Main Loop
def test_all_users():
    batch_size = 5
    current_offset = 0
    batch_count = 1

    print("🚀 Starting Full Database Evaluation...")

    while True:
        print(f"\n--- 📦 Processing Batch {batch_count} (Records {current_offset} to {current_offset + batch_size}) ---")
        
        # A. Get the Batch
        logs = get_db_logs(limit=batch_size, offset=current_offset)
        
        # B. Check if empty (Stop if no more users)
        if not logs:
            print("✅ No more users found in database. Testing Complete!")
            break

        test_cases = []

        # C. Process each user in this batch
        for row in logs:
            scores = {
                "deep_squat": row.deep_squat,
                "hurdle_step": row.hurdle_step,
                "inline_lunge": row.inline_lunge,
                "shoulder_mobility": row.shoulder_mobility,
                "active_straight_leg_raise": row.aslr,
                "trunk_stability_pushup": row.trunk_stability,
                "rotary_stability": row.rotary_stability,
                "pain_present": False 
            }

            # Run RAG
            print(f"   🔄 User ID {row.id}...")
            retrieval_output = get_exercises_by_profile(scores)
            retrieved_data = retrieval_output.get('data', [])
            
            retrieval_context = [
                f"{ex['exercise_name']}: {ex['description']}" for ex in retrieved_data
            ]

            plan_output = generate_workout_plan(retrieval_output.get('analysis', {}), retrieved_data)
            actual_output_text = f"Title: {plan_output['session_title']}\nSummary: {plan_output['coach_summary']}"

            # Create Test Case
            test_case = LLMTestCase(
                input=str(scores),
                actual_output=actual_output_text,
                retrieval_context=retrieval_context
            )
            test_cases.append(test_case)

        # D. Run Evaluation for this Batch
        # We recreate metrics each time to avoid caching issues
        faithfulness = FaithfulnessMetric(threshold=0.9, model=groq_evaluator, include_reason=True)
        relevancy = AnswerRelevancyMetric(threshold=0.9, model=groq_evaluator, include_reason=True)
        
        evaluate(test_cases, metrics=[faithfulness, relevancy])

        # E. Prepare for next loop
        current_offset += batch_size
        batch_count += 1
        
        # Optional: Sleep briefly to be nice to the API
        time.sleep(1)

if __name__ == "__main__":
    test_all_users()
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan

def test_full_system():
    print("\n" + "="*60)
    print(" 🏋️‍♂️  FMS 7-POINT RAG SYSTEM - FULL PIPELINE TEST  🏋️‍♂️")
    print("="*60)
    
    # --- SIMULATED USER INPUT (The "Bad Hips" Scenario) ---
    # User has a Perfect Squat (3), but Bad ASLR (1).
    user_profile = {
        "deep_squat": 3, 
        "hurdle_step": 2, 
        "inline_lunge": 2, 
        "shoulder_mobility": 2, 
        "active_straight_leg_raise": 1, # <--- The Limiting Factor
        "trunk_stability_pushup": 2, 
        "rotary_stability": 2
    }

    print("\n1️⃣  STEP 1: ANALYZING PROFILE...")
    print(f"   Input: {json.dumps(user_profile, indent=2)}")

    # 1. RETRIEVER (Runs the Analyzer + Fetches Data)
    retrieval_result = get_exercises_by_profile(user_profile)
    
    if retrieval_result['status'] == "STOP":
        print(f"\n🛑 STOP: {retrieval_result['message']}")
        return

    analysis = retrieval_result['analysis']
    exercises = retrieval_result['data']
    
    print(f"\n✅ ANALYSIS COMPLETE")
    print(f"   • Status: {analysis['status']}")
    print(f"   • Reason: {analysis['reason']}")
    print(f"   • Selected {len(exercises)} exercises.")

    # 2. GENERATOR (Formats the UI)
    print("\n2️⃣  STEP 2: GENERATING COACHING UI (LLM)...")
    
    try:
        ui_output = generate_workout_plan(analysis, exercises)
        
        print("\n" + "-"*20 + "  📱 FINAL APP OUTPUT  " + "-"*20)
        print(json.dumps(ui_output, indent=2))
        print("-" * 62)
        
    except Exception as e:
        print(f"\n💥 Generator Error: {e}")

if __name__ == "__main__":
    test_full_system()
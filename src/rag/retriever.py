import json
import os
import random
from src.logic.fms_analyzer import analyze_fms_profile

# Path to your JSON database
DB_PATH = 'data/processed/exercise_knowledge_base.json'

def load_knowledge_base():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_exercises_by_profile(fms_profile_scores):
    """
    1. Analyzes the full 7-test profile.
    2. Determines the safe Level (e.g., Level 5).
    3. Fetches exercises matching that Level.
    """
    
    # --- 1. RUN THE BRAIN ---
    analysis = analyze_fms_profile(fms_profile_scores)
    
    if analysis['status'] == "STOP":
        return {
            "status": "STOP",
            "message": analysis['reason'],
            "data": []
        }
    
    target_level = analysis['target_level']
    
    # --- 2. LOAD DATA ---
    kb = load_knowledge_base()
    
    # --- 3. FILTER BY TARGET LEVEL ---
    # We allow the target level AND one level above/below for variety, 
    # but strictly adhering to the logic helps. Let's stick to the target level exactly first.
    candidate_exercises = [
        ex for ex in kb 
        if ex.get('difficulty_level') == target_level
    ]
    
    # If exact level has no exercises, try +/- 1 level (Safety buffer)
    if not candidate_exercises:
         candidate_exercises = [
            ex for ex in kb 
            if abs(ex.get('difficulty_level') - target_level) <= 1
        ]

    # --- 4. SELECT (Shuffle) ---
    selected = random.sample(candidate_exercises, min(len(candidate_exercises), 3))
    
    return {
        "status": "SUCCESS",
        "analysis": analysis, # Pass the "Coach's Reasoning" back to the UI
        "data": selected
    }
# generator.py: Removed pain_present check (now handled per-test in analyzer).

import os
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- UI OUTPUT SCHEMA ---
class ExerciseCard(BaseModel):
    name: str = Field(description="Exact exercise name from database")
    tag: str = Field(description="Short uppercase badge, e.g. 'ANKLE MOBILITY', 'KNEE TRACKING'")
    sets_reps: str = Field(description="e.g. '3 x 10-12', '3 x 30s hold'")
    tempo: str = Field(description="e.g. '3-1-3-0', 'Controlled'")
    coach_tip: str = Field(description="1-2 sentence cue specifically addressing the athlete's high-severity faults.")

class WorkoutSession(BaseModel):
    session_title: str = Field(description="Concise title like 'Level 5 Ankle & Squat Patterning'")
    estimated_duration: str = Field(default="20-30 min", description="Approximate time")
    difficulty_color: str = Field(default="Green", description="Green, Yellow, Red")
    coach_summary: str = Field(description="2-4 sentence explanation of why these exercises were chosen.")
    exercises: List[ExerciseCard] = Field(default_factory=list, description="List of exercises")

# --- HELPER: FORMAT HIGH-SEVERITY FAULTS ---
def format_faults_for_prompt(full_data: Dict[str, Any]) -> str:
    """
    Summarizes only severe faults (>=3) with context.
    """
    fault_summary = []
    pain_detected = False  # Now check per-test

    for test_name, test_data in full_data.items():
        # Skip non-dictionary items
        if not isinstance(test_data, dict) or 'score' not in test_data:
            continue

        test_faults = []
        # Iterate over sub-categories (e.g., "trunk_torso", "lower_limb")
        for category, details in test_data.items():
            if isinstance(details, dict):
                for fault_name, severity in details.items():
                    # Check severity threshold
                    if isinstance(severity, (int, float)) and severity >= 3:
                        clean_name = fault_name.replace('_', ' ').title()
                        interpretation = ""
                        
                        # Add quick FMS context for the LLM
                        if 'heels_lift' in fault_name:
                            interpretation = "-> ankle restriction suspected"
                        elif 'knee_valgus' in fault_name:
                            interpretation = "-> glute weakness / motor control"
                        elif 'forward_lean' in fault_name:
                            interpretation = "-> thoracic/core weakness"
                        elif 'pain_reported' in fault_name and severity > 0:
                            pain_detected = True

                        test_faults.append(f"{clean_name} ({severity}/4) {interpretation}")

        if test_faults:
            # Format: "Deep Squat (Score 1/3): - Heels Lift (3/4)"
            clean_test = test_name.replace('_', ' ').title()
            fault_summary.append(f"**{clean_test}** (Score {test_data.get('score', '?')}/3):\n   - " + "\n   - ".join(test_faults))

    if pain_detected:
        return "PAIN DETECTED - STOP TRAINING. REFER TO MEDICAL PRO.\n" + "\n".join(fault_summary)
    
    return "\n\n".join(fault_summary) if fault_summary else "No severe faults (>=3/4) detected."

# --- MAIN GENERATOR FUNCTION ---
def generate_workout_plan(analysis_context: Dict[str, Any], exercises: List[Dict[str, Any]]):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"session_title": "Configuration Error", "coach_summary": "GROQ_API_KEY missing.", "exercises": []}

    # 1. Pain Override (Safety First) - Now based on analysis (per-test pain sets score=0, which triggers STOP in analyzer)
    if analysis_context.get('status') == "STOP":
        return {
            "session_title": "Medical Referral Required",
            "coach_summary": "Pain was reported during screening. Do NOT proceed with corrective exercise. Please consult a physical therapist or doctor.",
            "difficulty_color": "Red",
            "exercises": []
        }

    # 2. Empty List Check (CRITICAL FIX)
    # If retriever found nothing, do not call LLM. It will hallucinate.
    if not exercises:
        return {
            "session_title": "Assessment Complete - No Specific Drills",
            "coach_summary": "Based on the inputs, no specific corrective exercises were found in the database for this combination of faults and level. The athlete may be cleared for general training or requires a different database.",
            "difficulty_color": "Green",
            "exercises": []
        }

    # Sort for consistency
    exercises = sorted(exercises, key=lambda x: x.get('exercise_name', ''))

    # Setup LLM
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.0,  # Set to 0 for determinism
        api_key=api_key,
        model_kwargs={"seed": 42}
    )

    parser = JsonOutputParser(pydantic_object=WorkoutSession)

    # Format exercises for prompt
    exercise_text = "\n".join([
        f"- **{ex.get('exercise_name', 'Unknown')}** (Level {ex.get('difficulty_level', '?')})\n"
        f"  Tags: {', '.join(ex.get('tags', []))}\n"
        f"  Description: {ex.get('description', 'No description')}"
        for ex in exercises
    ])

    # Format faults
    faults_text = format_faults_for_prompt(analysis_context.get('detailed_faults', {}))

    # System Prompt
    system_prompt = """
    You are an expert FMS Strength Coach. Create a corrective workout plan.
    
    ### ATHLETE DATA
    - Status: {status}
    - Target Level: {level} ({reason})
    - Top Faults: 
    {faults_text}

    ### AVAILABLE EXERCISES (STRICT CONSTRAINT)
    You must construct the workout using ONLY the exercises listed below. Do not invent exercises.
    {exercise_list}

    ### INSTRUCTIONS
    1. **Selection:** Choose the best 2-3 exercises from the list that address the 'Top Faults'. Prioritize exercises whose tags directly match the faults (e.g., 'fix_knee_valgus' for knee valgus fault).
    2. **Cues:** Write a 'coach_tip' for each that specifically mentions the user's fault (e.g., "Squeeze glutes to stop knees caving in").
    3. **Difficulty:** - If Target Level <= 3, Color = Red. 
       - If Target Level 4-6, Color = Yellow.
       - If Target Level >= 7, Color = Green.
    4. **Output:** Return strict JSON matching the schema.

    {format_instructions}
    """

    prompt = ChatPromptTemplate.from_template(
        template=system_prompt,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt | llm | parser

    try:
        response = chain.invoke({
            "status": analysis_context.get('status', 'TRAINING'),
            "level": str(analysis_context.get('target_level', 1)),
            "reason": analysis_context.get('reason', 'General movement'),
            "faults_text": faults_text,
            "exercise_list": exercise_text
        })

        # Fallback for missing fields
        if 'difficulty_color' not in response:
            response['difficulty_color'] = 'Yellow'
        
        return response

    except Exception as e:
        return {
            "session_title": "Generation Error",
            "coach_summary": f"AI Generation failed: {str(e)}",
            "difficulty_color": "Red",
            "exercises": []
        }
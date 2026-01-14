import os
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# --- 1. DEFINE THE UI "BLUEPRINT" ---
class ExerciseCard(BaseModel):
    name: str = Field(description="The display name of the exercise")
    tag: str = Field(description="The UI badge. Use the 'Clinical Type' provided (e.g., 'Mobility', 'Stability').")
    sets_reps: str = Field(description="Prescription based on the phase (e.g., '2 sets x 12 reps' for Mobility, '5 sets x 3 reps' for Power).")
    tempo: str = Field(description="Tempo instructions (e.g., 'Slow & Controlled', 'Explosive').")
    coach_tip: str = Field(description="A specific cue derived from the exercise description.")

class WorkoutSession(BaseModel):
    session_title: str = Field(description="A professional title based on the goal (e.g., 'Hip Mobility Correction', 'Squat Power Block').")
    estimated_duration: str = Field(description="Total time, e.g., '15 Mins'")
    difficulty_color: str = Field(description="UI color code: 'Green' (Corrective), 'Yellow' (Stability), or 'Red' (Performance).")
    coach_summary: str = Field(description="A 1-sentence explanation of WHY this session was chosen.")
    exercises: List[ExerciseCard] = Field(description="The list of formatted exercise cards")

# --- 2. MAIN GENERATOR FUNCTION ---
def generate_workout_plan(analysis_context: Dict[str, Any], exercises: List[Dict[str, Any]]):
    """
    Generates the UI JSON.
    """
    
    # --- MOVED INSIDE: Initialize LLM only when called ---
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {
            "session_title": "Configuration Error",
            "difficulty_color": "Red",
            "coach_summary": "System Error: GROQ_API_KEY is missing from Cloud Secrets.",
            "exercises": []
        }

    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile", 
        temperature=0,
        api_key=api_key
    )
    
    parser = JsonOutputParser(pydantic_object=WorkoutSession)

    # --- 3. THE "COACH" PROMPT ---
    system_prompt = """
    You are an expert Strength & Conditioning Coach.
    Your goal is to format a raw list of exercises into a professional "Workout Card" for a mobile app.

    ### ATHLETE CONTEXT
    - **Clinical Status:** {status}
    - **Target Level:** {level}
    - **Coach's Logic:** "{reason}"

    ### THE SELECTED EXERCISES
    {exercise_list}

    ### INSTRUCTIONS
    1. **Do NOT change the exercises.** Use exactly the 3 provided in the list.
    2. **Generate specific cues:** Read the provided 'description' for each exercise to write the 'coach_tip'.
    3. **Set Parameters:** - If Status is 'MOBILITY': Use higher reps (10-15), slow tempo, Green color.
       - If Status is 'STABILITY': Use moderate reps (8-10), 'Hold' tempo, Yellow color.
       - If Status is 'POWER/STRENGTH': Use lower reps (3-5), explosive tempo, Red color.
    4. **Session Title:** Create a title that reflects the "Coach's Logic" (e.g., if logic mentions "ASLR restriction", title is "Hip Mobility Reset").

    {format_instructions}
    """

    # Format the input list to include the description so the LLM can use it
    exercise_text = "\n".join([
        f"- Name: {ex['exercise_name']} | Type: {ex.get('clinical_type', 'General')} | Desc: {ex.get('description', '')}" 
        for ex in exercises
    ])

    prompt = ChatPromptTemplate.from_template(
        template=system_prompt,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    try:
        response = chain.invoke({
            "status": analysis_context.get('status', 'TRAINING'),
            "level": str(analysis_context.get('target_level', 1)),
            "reason": analysis_context.get('reason', 'General training'),
            "exercise_list": exercise_text
        })
        return response
    except Exception as e:
        # Return a safe error structure so the UI doesn't crash
        return {
            "session_title": "AI Error",
            "difficulty_color": "Red",
            "coach_summary": f"Generation failed: {str(e)}",
            "exercises": []
        }
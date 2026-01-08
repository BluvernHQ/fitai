import streamlit as st
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- IMPORT YOUR BRAIN DIRECTLY (No API URL needed) ---
# We bypass main.py and call the logic functions directly
from src.rag.retriever import get_exercises_by_profile
from src.rag.generator import generate_workout_plan
from src.database import AssessmentLog  # Import the DB model

# 1. CONFIG & SETUP
st.set_page_config(page_title="FMS Smart Coach", page_icon="🏋️", layout="wide")
load_dotenv()

# Setup Database Connection (Neon)
DB_URL = os.getenv("DATABASE_URL")
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = None
SessionLocal = None
if DB_URL:
    try:
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(bind=engine)
    except Exception as e:
        st.warning(f"Database connection skipped: {e}")

# --- HEADER ---
st.title("🏋️ AI Strength Coach: FMS Analyzer")
st.markdown("### From Screening to Programming in Seconds")
st.markdown("---")

# --- SIDEBAR: INPUT FORM ---
with st.sidebar:
    st.header("📝 Athlete Scorecard")
    
    deep_squat = st.slider("1. Deep Squat", 0, 3, 2)
    hurdle_step = st.slider("2. Hurdle Step", 0, 3, 2)
    inline_lunge = st.slider("3. Inline Lunge", 0, 3, 2)
    shoulder_mobility = st.slider("4. Shoulder Mobility", 0, 3, 2)
    aslr = st.slider("5. Active Straight Leg Raise", 0, 3, 2)
    trunk_stability = st.slider("6. Trunk Stability Pushup", 0, 3, 2)
    rotary_stability = st.slider("7. Rotary Stability", 0, 3, 2)
    
    st.markdown("---")
    pain_present = st.toggle("⚠️ Pain Present during testing?", value=False)
    
    submit_btn = st.button("🚀 Generate Workout Plan", type="primary", use_container_width=True)

# --- MAIN LOGIC ---
if submit_btn:
    # 1. Prepare Data
    scores = {
        "deep_squat": deep_squat,
        "hurdle_step": hurdle_step,
        "inline_lunge": inline_lunge,
        "shoulder_mobility": shoulder_mobility,
        "active_straight_leg_raise": aslr,
        "trunk_stability_pushup": trunk_stability,
        "rotary_stability": rotary_stability,
        "pain_present": pain_present
    }

    with st.spinner("🤖 AI Coach is analyzing the profile..."):
        try:
            # --- LOGIC BRANCH A: PAIN DETECTED ---
            if pain_present:
                result_data = {
                    "session_title": "Medical Referral Required",
                    "difficulty_color": "Red",
                    "coach_summary": "Pain reported during screening. Training is contraindicated.",
                    "exercises": []
                }
            else:
                # --- LOGIC BRANCH B: RUN RAG ENGINE DIRECTLY ---
                # Step 1: Retrieve (Get Rules & Exercises)
                retrieval_result = get_exercises_by_profile(scores)
                
                if retrieval_result['status'] == "STOP":
                    result_data = {
                        "session_title": "Medical Referral Required",
                        "difficulty_color": "Red",
                        "coach_summary": retrieval_result['message'],
                        "exercises": []
                    }
                else:
                    # Step 2: Generate (Call LLM)
                    analysis = retrieval_result['analysis']
                    ex_data = retrieval_result['data']
                    result_data = generate_workout_plan(analysis, ex_data)

            # --- DISPLAY RESULTS ---
            color_map = {"Green": "green", "Yellow": "orange", "Red": "red"}
            ui_color = color_map.get(result_data.get("difficulty_color", "Green"), "blue")
            
            st.subheader(f"🎯 Target Session: :{ui_color}[{result_data['session_title']}]")
            st.info(f"**Coach's Logic:** {result_data['coach_summary']}")
            
            # Exercise Cards
            st.markdown("### 📋 Prescribed Exercises")
            if not result_data['exercises']:
                st.error("No exercises assigned (Medical Referral or Stop).")
            else:
                cols = st.columns(3)
                for idx, exercise in enumerate(result_data['exercises']):
                    with cols[idx % 3]: # Wrap around columns if > 3 exercises
                        st.markdown(f"""
                        <div style="padding: 15px; border: 1px solid #444; border-radius: 10px; background-color: #262730; margin-bottom: 10px;">
                            <h4 style="color: #FF4B4B; margin:0;">{exercise['name']}</h4>
                            <span style="background-color: #333; padding: 2px 6px; border-radius: 4px; font-size: 0.8em;">{exercise['tag']}</span>
                            <p style="margin-top: 10px; font-size: 0.95em;"><b>Rx:</b> {exercise['sets_reps']}<br>
                            <b>Tempo:</b> {exercise['tempo']}</p>
                            <hr style="margin: 5px 0;">
                            <p style="font-style: italic; font-size: 0.85em; color: #aaa;">💡 "{exercise['coach_tip']}"</p>
                        </div>
                        """, unsafe_allow_html=True)

            # --- SAVE TO NEON DATABASE ---
            if SessionLocal:
                try:
                    session = SessionLocal()
                    # Calculate simple total for DB record
                    total_score = sum([v for k,v in scores.items() if isinstance(v, int)])
                    
                    new_log = AssessmentLog(
                        deep_squat=deep_squat, hurdle_step=hurdle_step, inline_lunge=inline_lunge,
                        shoulder_mobility=shoulder_mobility, aslr=aslr, trunk_stability=trunk_stability,
                        rotary_stability=rotary_stability, final_score=total_score, 
                        predicted_level=result_data['session_title']
                    )
                    session.add(new_log)
                    session.commit()
                    session.close()
                    st.toast("✅ Results saved to Athlete History (Neon DB)", icon="💾")
                except Exception as e:
                    st.error(f"DB Save Error: {e}")

        except Exception as e:
            st.error(f"❌ System Error: {str(e)}")
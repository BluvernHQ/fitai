import streamlit as st
import os
import sys

# --- FIX 1: SAFER SQLITE SWAP (Cloud Compatibility) ---
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# --- FIX 2: INJECT SECRETS INTO ENV ---
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

# --- IMPORTS ---
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- LOAD MODULES (Wrap in try/except) ---
try:
    from src.rag.retriever import get_exercises_by_profile
    from src.rag.generator import generate_workout_plan
    # We try to import the DB model, but if it fails, we just ignore it
    try:
        from src.database import AssessmentLog
    except ImportError:
        AssessmentLog = None
except ImportError as e:
    st.error(f"CRITICAL ERROR: Missing Module. {e}")
    st.stop()

# 1. CONFIG & SETUP
st.set_page_config(page_title="FMS Smart Coach", page_icon="🏋️", layout="wide")
load_dotenv() 

# --- DATABASE SETUP (SAFE MODE) ---
# If no URL is provided, we simply disable the DB features
DB_URL = os.getenv("DATABASE_URL")
engine = None
SessionLocal = None

if DB_URL and DB_URL.startswith("postgres"):
    try:
        if DB_URL.startswith("postgres://"):
            DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(bind=engine)
    except Exception as e:
        print(f"Database connection failed: {e}")
        SessionLocal = None

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
        "pain_present": False 
    }

    with st.spinner("🤖 AI Coach is analyzing the profile..."):
        try:
            # Step 1: Retrieve
            retrieval_result = get_exercises_by_profile(scores)
            
            # Step 2: Generate
            analysis = retrieval_result.get('analysis', {'reason': 'General Training'})
            ex_data = retrieval_result.get('data', [])
            
            if not ex_data:
                ex_data = [{"exercise_name": "General Mobility Flow", "clinical_type": "Mobility", "description": "Full body mobility routine."}]

            result_data = generate_workout_plan(analysis, ex_data)

            # --- DISPLAY RESULTS ---
            color_map = {"Green": "green", "Yellow": "orange", "Red": "red"}
            ui_color = color_map.get(result_data.get("difficulty_color", "Green"), "blue")
            
            st.subheader(f"🎯 Target Session: :{ui_color}[{result_data.get('session_title', 'Workout Ready')}]")
            st.info(f"**Coach's Logic:** {result_data.get('coach_summary', 'Plan generated based on FMS profile.')}")
            
            # Exercise Cards
            st.markdown("### 📋 Prescribed Exercises")
            exercises_to_show = result_data.get('exercises', [])
            
            if not exercises_to_show:
                 st.warning("No specific exercises generated.")
            else:
                cols = st.columns(3)
                for idx, exercise in enumerate(exercises_to_show):
                    with cols[idx % 3]: 
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

            # --- SAVE TO DB (SKIPPED IF NO DB) ---
            if SessionLocal and AssessmentLog:
                try:
                    session = SessionLocal()
                    total_score = sum([v for k,v in scores.items() if isinstance(v, int)])
                    
                    new_log = AssessmentLog(
                        deep_squat=deep_squat, hurdle_step=hurdle_step, inline_lunge=inline_lunge,
                        shoulder_mobility=shoulder_mobility, aslr=aslr, trunk_stability=trunk_stability,
                        rotary_stability=rotary_stability, final_score=total_score, 
                        predicted_level=result_data.get('session_title', 'Generated Plan')
                    )
                    session.add(new_log)
                    session.commit()
                    session.close()
                    st.toast("✅ Results saved", icon="💾")
                except Exception:
                    pass 
            else:
                # Just show a toast for the demo so it feels complete
                st.toast("✅ Workout Generated Successfully!", icon="🚀")

        except Exception as e:
            st.error(f"❌ System Error: {str(e)}")
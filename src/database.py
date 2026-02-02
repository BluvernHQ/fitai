import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from datetime import datetime

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback for Streamlit Cloud if .env isn't found (it uses secrets)
    import streamlit as st
    try:
        DATABASE_URL = st.secrets["DATABASE_URL"]
    except:
        pass

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check .env or Streamlit Secrets.")

# Ensure async driver
if "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"ssl": "require"}
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# --- TABLES ---

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    corrective_category = Column(String)
    fms_profile = Column(String)
    description = Column(Text)
    video_url = Column(String, nullable=True)

class AssessmentLog(Base):
    __tablename__ = "assessment_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # 1. Deep Squat
    deep_squat_score = Column(Integer)
    deep_squat_details = Column(JSON) # Stores all sub-inputs like "heels_lift"

    # 2. Hurdle Step
    hurdle_step_l = Column(Integer)
    hurdle_step_r = Column(Integer)
    hurdle_step_final = Column(Integer)
    hurdle_step_details = Column(JSON)

    # 3. Inline Lunge
    inline_lunge_l = Column(Integer)
    inline_lunge_r = Column(Integer)
    inline_lunge_final = Column(Integer)
    inline_lunge_details = Column(JSON)

    # 4. Shoulder Mobility
    shoulder_mobility_l = Column(Integer)
    shoulder_mobility_r = Column(Integer)
    shoulder_clearing_pain = Column(Boolean)
    shoulder_mobility_final = Column(Integer)
    shoulder_mobility_details = Column(JSON)

    # 5. ASLR
    aslr_l = Column(Integer)
    aslr_r = Column(Integer)
    aslr_final = Column(Integer)
    aslr_details = Column(JSON)

    # 6. Trunk Stability
    trunk_stability_raw = Column(Integer)
    extension_clearing_pain = Column(Boolean)
    trunk_stability_final = Column(Integer)
    trunk_stability_details = Column(JSON)

    # 7. Rotary Stability
    rotary_stability_l = Column(Integer)
    rotary_stability_r = Column(Integer)
    flexion_clearing_pain = Column(Boolean)
    rotary_stability_final = Column(Integer)
    rotary_stability_details = Column(JSON)

    # Outputs
    total_fms_score = Column(Integer)
    predicted_level = Column(String)
    analysis_summary = Column(Text)
    final_plan_json = Column(Text)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
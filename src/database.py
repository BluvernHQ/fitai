import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 1. Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Ensure using async driver (fix for the SSL/Async issue we solved earlier)
if DATABASE_URL and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create Engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"ssl": "require"} # NeonDB requires SSL
)

# Session Factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# ==========================================
# 2. Table Definitions
# ==========================================

# RAG Knowledge Base Table (Keep this for your exercises!)
class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    corrective_category = Column(String)  # e.g., "Mobility", "Stability"
    fms_profile = Column(String)          # e.g., "Deep Squat: 1"
    description = Column(Text)
    video_url = Column(String, nullable=True)

# User Assessment Logs (Updated with SUB-INPUTS)
class AssessmentLog(Base):
    __tablename__ = "assessment_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # --- INPUTS (FMS Scores) ---
    deep_squat_score = Column(Integer)

    hurdle_step_l = Column(Integer)
    hurdle_step_r = Column(Integer)
    hurdle_step_final = Column(Integer)

    inline_lunge_l = Column(Integer)
    inline_lunge_r = Column(Integer)
    inline_lunge_final = Column(Integer)

    shoulder_mobility_l = Column(Integer)
    shoulder_mobility_r = Column(Integer)
    shoulder_clearing_pain = Column(Boolean, default=False)
    shoulder_mobility_final = Column(Integer)

    aslr_l = Column(Integer)
    aslr_r = Column(Integer)
    aslr_final = Column(Integer)

    trunk_stability_raw = Column(Integer)
    extension_clearing_pain = Column(Boolean, default=False)
    trunk_stability_final = Column(Integer)

    rotary_stability_l = Column(Integer)
    rotary_stability_r = Column(Integer)
    flexion_clearing_pain = Column(Boolean, default=False)
    rotary_stability_final = Column(Integer)

    total_fms_score = Column(Integer)
    predicted_level = Column(String)

    # --- NEW: OUTPUTS (Rag Generation) ---
    analysis_summary = Column(Text)  # To store the LLM analysis text
    final_plan_json = Column(Text)   # To store the full workout plan (as a string)

# ==========================================
# 3. Helper Functions
# ==========================================

async def init_db():
    """Create tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for DB session."""
    async with AsyncSessionLocal() as session:
        yield session
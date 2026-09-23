import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, JSON, Float, Text, UniqueConstraint
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env file")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("sqlite://") and "+aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    students = relationship("Student", back_populates="coach")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    days_per_week = Column(Integer, default=3)
    equipment = Column(JSON, default=list)
    injuries = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    coach = relationship("Coach", back_populates="students")
    lift_maxes = relationship("LiftMax", back_populates="student", cascade="all, delete-orphan")
    lift_max_logs = relationship("LiftMaxLog", back_populates="student", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="student")


class LiftMax(Base):
    __tablename__ = "lift_maxes"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    lift_key = Column(String, nullable=False)
    one_rm = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="lift_maxes")


class LiftMaxLog(Base):
    __tablename__ = "lift_max_logs"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    lift_key = Column(String, nullable=False, index=True)
    one_rm = Column(Float, nullable=False)
    previous_one_rm = Column(Float, nullable=True)
    source = Column(String, default="coach")
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    student = relationship("Student", back_populates="lift_max_logs")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    assessment_kind = Column(String, default="baseline_session")
    selected_batteries = Column(JSON, default=list)
    raw_json_data = Column(JSON)
    scores = Column(JSON)
    comments = Column(JSON)
    needs = Column(JSON)
    findings = Column(JSON)
    total_score = Column(Integer)
    status = Column(String)

    student = relationship("Student", back_populates="assessments")
    programs = relationship("ProgramDraft", back_populates="assessment")


class TrainingBlock(Base):
    __tablename__ = "training_blocks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    status = Column(String, default="active")
    week_count = Column(Integer, default=4)
    current_week = Column(Integer, default=1)
    methodology_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProgramDraft(Base):
    __tablename__ = "program_drafts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    status = Column(String, default="draft")
    ai_plan = Column(JSON, nullable=False)
    coach_plan = Column(JSON, nullable=True)
    candidate_exercises = Column(JSON, default=dict)
    context_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    block_id = Column(Integer, ForeignKey("training_blocks.id"), nullable=True, index=True)
    week_index = Column(Integer, default=1)
    snapshot_immutable = Column(Boolean, default=False)

    assessment = relationship("Assessment", back_populates="programs")


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("program_drafts.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PreferenceEvent(Base):
    __tablename__ = "preference_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_preference_event_id"),)

    id = Column(Integer, primary_key=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("program_drafts.id"), nullable=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
    context_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    event_id = Column(String, nullable=True, index=True)
    reason_code = Column(String, nullable=True)


class PlatformModule(Base):
    __tablename__ = "platform_modules"

    id = Column(Integer, primary_key=True)
    module_id = Column(String, unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    config = Column(JSON, default=dict)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CoachExercisePrior(Base):
    __tablename__ = "coach_exercise_priors"

    id = Column(Integer, primary_key=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    exercise_id = Column(String, nullable=False)
    context_key = Column(String, default="")
    shown = Column(Integer, default=0)
    kept = Column(Integer, default=0)
    replaced = Column(Integer, default=0)


# Legacy tables kept so old SQLite rows remain readable
class AssessmentInput(Base):
    __tablename__ = "assessment_inputs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_json_data = Column(JSON)
    scores = relationship("AssessmentScore", back_populates="input_data", uselist=False)


class AssessmentScore(Base):
    __tablename__ = "assessment_scores"

    id = Column(Integer, primary_key=True, index=True)
    input_id = Column(Integer, ForeignKey("assessment_inputs.id"))
    overhead_squat = Column(Integer)
    hurdle_step = Column(Integer)
    inline_lunge = Column(Integer)
    shoulder_mobility = Column(Integer)
    active_straight_leg_raise = Column(Integer)
    trunk_stability_pushup = Column(Integer)
    rotary_stability = Column(Integer)
    total_score = Column(Integer)
    generated_workout = Column(JSON, nullable=True)
    input_data = relationship("AssessmentInput", back_populates="scores")

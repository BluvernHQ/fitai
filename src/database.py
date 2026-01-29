# src/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

engine = create_async_engine(settings.DATABASE_URL, echo=True)  # echo=True for debug logs
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Example table (adjust columns as needed)
class FMSResult(Base):
    __tablename__ = "fms_results"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    input_profile = Column(JSON, nullable=False)          # full input JSON
    effective_scores = Column(JSON, nullable=True)
    analysis = Column(JSON, nullable=True)
    exercises = Column(JSON, nullable=True)
    final_plan = Column(JSON, nullable=True)             # full output

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Call this once on startup (see main.py below)
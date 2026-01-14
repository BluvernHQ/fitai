from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class AssessmentLog(Base):
    __tablename__ = "assessment_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # FMS Scores
    deep_squat = Column(Integer)
    hurdle_step = Column(Integer)
    inline_lunge = Column(Integer)
    shoulder_mobility = Column(Integer)
    aslr = Column(Integer)
    trunk_stability = Column(Integer)
    rotary_stability = Column(Integer)
    
    final_score = Column(Integer)
    predicted_level = Column(String)
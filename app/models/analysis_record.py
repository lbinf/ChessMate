from app.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

class AnalysisRecord(Base):
    __tablename__ = 'analysis_records'
    id = Column(Integer, primary_key=True, index=True)
    fen = Column(String(100), nullable=False)
    best_move = Column(String(10))
    result_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow) 
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AnalysisLogs(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP, nullable=True)
    level = Column(String(10), nullable=True)
    message = Column(Text, nullable=True)


from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib
import json

Base = declarative_base()

class RawEvent(Base):
    """Immutable log of all raw events received"""
    __tablename__ = 'raw_events'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100), nullable=False, index=True)
    raw_payload = Column(String(5000), nullable=False)  # JSON string
    content_hash = Column(String(64), nullable=False, unique=True)  # SHA256 hash
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    processing_status = Column(String(20), default='pending')  # pending, processed, failed
    error_message = Column(String(500), nullable=True)

class NormalizedEvent(Base):
    """Canonical normalized events"""
    __tablename__ = 'normalized_events'
    
    id = Column(Integer, primary_key=True)
    raw_event_id = Column(Integer, nullable=False, unique=True)  # Foreign key - ensures 1:1
    client_id = Column(String(100), nullable=False, index=True)
    metric = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    normalized_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        Index('idx_client_metric_time', 'client_id', 'metric', 'timestamp'),
    )

class FailedEvent(Base):
    """Track events that failed normalization"""
    __tablename__ = 'failed_events'
    
    id = Column(Integer, primary_key=True)
    raw_event_id = Column(Integer, nullable=False)
    client_id = Column(String(100), nullable=False)
    reason = Column(String(500), nullable=False)
    failed_at = Column(DateTime, default=datetime.utcnow)
    raw_payload = Column(String(5000), nullable=False)
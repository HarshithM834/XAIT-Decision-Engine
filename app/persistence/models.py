import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.persistence.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    record_id = Column(String, index=True, nullable=False)
    source = Column(String, nullable=False)
    current_stage = Column(String, nullable=False, default="received")
    status = Column(String, nullable=False, default="pending")
    request_hash = Column(String, index=True, nullable=True) # for idempotency
    
    # Payload capture
    payload = Column(JSON, nullable=True)
    
    # Decision Summary
    approval_required = Column(Boolean, nullable=True)
    review_required = Column(Boolean, nullable=True)
    final_decision = Column(String, nullable=True)
    rationale = Column(String, nullable=True)
    next_action = Column(String, nullable=True)
    
    last_error = Column(String, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    events = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    triggered_rules = relationship("TriggeredRule", back_populates="run", cascade="all, delete-orphan")
    job_executions = relationship("JobExecution", back_populates="run", cascade="all, delete-orphan")

class RunEvent(Base):
    __tablename__ = "run_events"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    stage = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    run = relationship("Run", back_populates="events")

class TriggeredRule(Base):
    __tablename__ = "triggered_rules"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    rule_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    decision_effect = Column(String, nullable=False)
    priority = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    
    run = relationship("Run", back_populates="triggered_rules")

class JobExecution(Base):
    __tablename__ = "job_executions"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    job_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    
    run = relationship("Run", back_populates="job_executions")

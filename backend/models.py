"""SQLAlchemy ORM models for claims, validation findings, alerts, and audit trail."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base

class ClaimModel(Base):
    """Database model for ingested and processed healthcare claims."""
    __tablename__ = "claims"

    claim_id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), nullable=False, index=True)
    provider_id = Column(String(64), nullable=False, index=True)
    service_date = Column(String(32), nullable=False)
    submission_timestamp = Column(String(64), nullable=False)
    diagnosis_code = Column(String(32), nullable=True)
    procedure_code = Column(String(32), nullable=True)
    claim_amount = Column(Float, nullable=False, default=0.0)
    service_lines_count = Column(Integer, nullable=False, default=1)
    injected_scenario = Column(String(64), nullable=True, default="normal")

    # Processing outputs
    processing_status = Column(String(32), nullable=False, default="PENDING")  # PROCESSED, ERROR, PENDING
    category = Column(String(32), nullable=False, default="REVIEW")            # READY, CORRECTION, REVIEW
    triage_score = Column(Float, nullable=False, default=0.0)                 # 0 - 100 triage priority
    review_state = Column(String(32), nullable=False, default="PENDING")      # PENDING, ACKNOWLEDGED, RESOLVED
    anomaly_evidence_json = Column(Text, nullable=True)                       # Serialized JSON of anomaly factors
    created_at = Column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())

    # Relationships
    findings = relationship("ValidationFindingModel", back_populates="claim", cascade="all, delete-orphan")
    alerts = relationship("AlertModel", back_populates="claim", cascade="all, delete-orphan")
    audit_events = relationship("AuditEventModel", back_populates="claim", cascade="all, delete-orphan")


class ValidationFindingModel(Base):
    """Deterministic validation rule evaluation result."""
    __tablename__ = "validation_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(64), ForeignKey("claims.claim_id"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    field = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False, default="INFO")  # ERROR, WARNING, INFO
    passed = Column(Boolean, nullable=False, default=True)

    claim = relationship("ClaimModel", back_populates="findings")


class AlertModel(Base):
    """Triage alerts generated when anomalies or validation flags occur."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(64), ForeignKey("claims.claim_id"), nullable=False, index=True)
    alert_type = Column(String(64), nullable=False)
    priority = Column(Float, nullable=False, default=0.0)
    description = Column(Text, nullable=False)
    created_at = Column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())

    claim = relationship("ClaimModel", back_populates="alerts")


class AuditEventModel(Base):
    """Immutable audit trail recording every state change and reviewer decision."""
    __tablename__ = "audit_trail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    claim_id = Column(String(64), ForeignKey("claims.claim_id"), nullable=False, index=True)
    action = Column(String(32), nullable=False)       # INGEST, VALIDATE, SCORE, ACKNOWLEDGE, RESOLVE
    disposition = Column(String(32), nullable=True)   # READY, CORRECTION, REVIEW
    reviewer_id = Column(String(64), nullable=True)   # e.g. "REV-101" or "SYSTEM"
    notes = Column(Text, nullable=True)
    timestamp = Column(String(64), default=lambda: datetime.now(timezone.utc).isoformat())

    claim = relationship("ClaimModel", back_populates="audit_events")

"""Pydantic schemas and DTOs representing the agreed JSON contract."""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------
# Ingestion / Raw Input Schema
# ---------------------------------------------------------
class ClaimInput(BaseModel):
    """Raw claim submitted for ingestion."""
    claim_id: str = Field(..., description="Unique claim identifier, e.g. CLM-2026-0001")
    patient_id: str = Field(..., description="Synthetic patient identifier")
    provider_id: str = Field(..., description="Synthetic provider identifier")
    service_date: str = Field(..., description="Date of service in YYYY-MM-DD")
    submission_timestamp: str = Field(..., description="ISO 8601 timestamp of claim submission")
    diagnosis_code: Optional[str] = Field(None, description="Primary ICD-10 diagnosis code")
    procedure_code: Optional[str] = Field(None, description="Primary CPT/HCPCS procedure code")
    claim_amount: float = Field(..., description="Total billed amount in USD")
    service_lines_count: int = Field(1, description="Number of service line items")
    injected_scenario: Optional[str] = Field("normal", description="Test scenario indicator: normal, high_amount, duplicate, missing_field")

    @field_validator("claim_id", "patient_id", "provider_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be empty")
        return v.strip()


# ---------------------------------------------------------
# Validation Findings & Evidence Schemas
# ---------------------------------------------------------
class ValidationFinding(BaseModel):
    rule_id: str
    field: str
    message: str
    severity: Literal["ERROR", "WARNING", "INFO"]
    passed: bool


class AnomalyEvidence(BaseModel):
    is_anomaly: bool = False
    model_score: float = 0.0          # Raw model output (decision_function or distance)
    normalized_score: float = 0.0     # 0 - 100 scaled anomaly intensity
    factors: List[str] = Field(default_factory=list)
    inference_latency_ms: float = 0.0
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    execution_target: str = "LOCAL_MOCK"  # LOCAL_MOCK | IBM_LINUXONE


# ---------------------------------------------------------
# Full Claim Record Schema
# ---------------------------------------------------------
class ReviewerDecision(BaseModel):
    decision: Literal["READY", "CORRECTION", "REVIEW"]
    notes: Optional[str] = ""
    reviewer_id: str
    timestamp: str


class ClaimRecord(BaseModel):
    claim_id: str
    patient_id: str
    provider_id: str
    service_date: str
    submission_timestamp: str
    diagnosis_code: Optional[str] = None
    procedure_code: Optional[str] = None
    claim_amount: float
    service_lines_count: int
    injected_scenario: Optional[str] = "normal"
    
    # Engine outputs
    processing_status: Literal["PROCESSED", "ERROR", "PENDING"] = "PROCESSED"
    category: Literal["READY", "CORRECTION", "REVIEW"]
    triage_score: float = Field(..., ge=0.0, le=100.0, description="0-100 triage priority index")
    validation_findings: List[ValidationFinding] = Field(default_factory=list)
    anomaly_evidence: AnomalyEvidence
    execution_target: str = "LOCAL_MOCK"
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    
    # Review workflow state
    review_state: Literal["PENDING", "ACKNOWLEDGED", "RESOLVED"] = "PENDING"
    reviewer_decision: Optional[ReviewerDecision] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------
# Reviewer Action Schema
# ---------------------------------------------------------
class ReviewerActionRequest(BaseModel):
    action: Literal["ACKNOWLEDGE", "RESOLVE"]
    disposition: Optional[Literal["READY", "CORRECTION", "REVIEW"]] = None
    reviewer_id: str = Field(..., min_length=1)
    notes: Optional[str] = ""


class ReviewerActionResponse(BaseModel):
    success: bool
    claim_id: str
    review_state: Literal["PENDING", "ACKNOWLEDGED", "RESOLVED"]
    disposition: Optional[Literal["READY", "CORRECTION", "REVIEW"]] = None
    audit_event_id: str
    timestamp: str


# ---------------------------------------------------------
# WebSocket Message Envelope
# ---------------------------------------------------------
class WebSocketEnvelope(BaseModel):
    event: Literal["CLAIM_SCORED", "CLAIM_ACTIONED", "STREAM_METRICS"]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any]

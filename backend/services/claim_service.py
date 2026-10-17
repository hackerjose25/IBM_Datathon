"""Claim orchestration service: validation, scoring, persistence, and audit tracking."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.schemas import (
    ClaimInput,
    ClaimRecord,
    ValidationFinding,
    AnomalyEvidence,
    ReviewerActionRequest,
    ReviewerActionResponse,
    ReviewerDecision,
)
from backend.models import (
    ClaimModel,
    ValidationFindingModel,
    AlertModel,
    AuditEventModel,
)
from backend.rules.validator import ClaimValidator
from backend.ml.inference import detector
from backend.services.stream_manager import stream_manager
from backend.config import settings

class ClaimService:
    """Coordinates validation, ML scoring, database persistence, and review events."""

    @staticmethod
    async def process_claim(claim_input: ClaimInput, db: Session) -> ClaimRecord:
        """
        Processes an incoming claim end-to-end:
        1. Deterministic validation
        2. ML anomaly inference
        3. Triage score and category routing
        4. DB persistence
        5. Live WebSocket event broadcast
        """
        if db.get(ClaimModel, claim_input.claim_id):
            raise ValueError("Claim ID already exists; replay rejected without changing the original or its review")
        # 1. Deterministic Validation
        findings, has_error, is_duplicate = ClaimValidator.validate_claim(claim_input, db=db)

        # 2. ML Anomaly Scoring
        anomaly_evidence: AnomalyEvidence = detector.predict(claim_input)

        # 3. Triage Category & Score Determination
        # Category Precedence:
        # If deterministic error present -> CORRECTION
        # Else if duplicate or anomaly detected -> REVIEW
        # Else -> READY
        processing_status = "ERROR" if anomaly_evidence.inference_error else "PROCESSED"
        if anomaly_evidence.inference_error:
            category = "REVIEW"
            triage_score = 100.0
        elif has_error:
            category = "CORRECTION"
            triage_score = max(55.0, anomaly_evidence.normalized_score)
        elif is_duplicate or anomaly_evidence.is_anomaly or anomaly_evidence.normalized_score >= settings.ANOMALY_THRESHOLD_SCORE:
            category = "REVIEW"
            triage_score = max(70.0, anomaly_evidence.normalized_score)
        else:
            category = "READY"
            triage_score = min(25.0, anomaly_evidence.normalized_score)

        triage_score = round(float(triage_score), 1)

        # 4. Construct DB Record
        db_claim = ClaimModel(
            claim_id=claim_input.claim_id,
            patient_id=claim_input.patient_id,
            provider_id=claim_input.provider_id,
            service_date=claim_input.service_date,
            submission_timestamp=claim_input.submission_timestamp,
            diagnosis_code=claim_input.diagnosis_code,
            procedure_code=claim_input.procedure_code,
            claim_amount=claim_input.claim_amount,
            service_lines_count=claim_input.service_lines_count,
            injected_scenario=claim_input.injected_scenario,
            processing_status=processing_status,
            category=category,
            triage_score=triage_score,
            review_state="PENDING",
            anomaly_evidence_json=anomaly_evidence.model_dump_json(),
        )

        db.merge(db_claim)

        # Persist findings
        for f in findings:
            finding_model = ValidationFindingModel(
                claim_id=claim_input.claim_id,
                rule_id=f.rule_id,
                field=f.field,
                message=f.message,
                severity=f.severity,
                passed=f.passed,
            )
            db.add(finding_model)

        # If flagged for CORRECTION or REVIEW, generate alert
        if category in ("CORRECTION", "REVIEW"):
            alert_desc = (
                f"Validation issue: {next(f.message for f in findings if not f.passed and f.severity == 'ERROR')}" if has_error
                else f"Anomaly flagged with priority {triage_score}/100"
            )
            alert_model = AlertModel(
                claim_id=claim_input.claim_id,
                alert_type="DETERMINISTIC_ERROR" if has_error else "ANOMALY_RISK",
                priority=triage_score,
                description=alert_desc,
            )
            db.add(alert_model)

        # Initial audit log event
        audit_event = AuditEventModel(
            event_id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            claim_id=claim_input.claim_id,
            action="INGEST_AND_SCORE",
            disposition=category,
            reviewer_id="SYSTEM",
            notes=f"Processed with priority {triage_score}/100 and routed to {category}.",
        )
        db.add(audit_event)

        db.commit()

        # Build output record with explicit execution target and latency percentiles
        record = ClaimRecord(
            claim_id=claim_input.claim_id,
            patient_id=claim_input.patient_id,
            provider_id=claim_input.provider_id,
            service_date=claim_input.service_date,
            submission_timestamp=claim_input.submission_timestamp,
            diagnosis_code=claim_input.diagnosis_code,
            procedure_code=claim_input.procedure_code,
            claim_amount=claim_input.claim_amount,
            service_lines_count=claim_input.service_lines_count,
            injected_scenario=claim_input.injected_scenario,
            processing_status=processing_status,
            category=category,
            triage_score=triage_score,
            validation_findings=findings,
            anomaly_evidence=anomaly_evidence,
            execution_target=settings.EXECUTION_TARGET,
            latency_p50_ms=anomaly_evidence.latency_p50_ms,
            latency_p95_ms=anomaly_evidence.latency_p95_ms,
            review_state="PENDING",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # 5. Broadcast to WebSocket clients
        await stream_manager.broadcast("CLAIM_SCORED", record.model_dump())

        return record

    @staticmethod
    async def apply_reviewer_action(
        claim_id: str,
        request: ReviewerActionRequest,
        db: Session
    ) -> ReviewerActionResponse:
        """Applies a human reviewer disposition or acknowledgement with full audit trail."""
        claim = db.query(ClaimModel).filter(ClaimModel.claim_id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        event_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        if request.action == "ACKNOWLEDGE":
            claim.review_state = "ACKNOWLEDGED"
        elif request.action == "RESOLVE":
            if not request.disposition:
                raise ValueError("RESOLVE requires a disposition")
            claim.review_state = "RESOLVED"

        # Record audit event
        audit_event = AuditEventModel(
            event_id=event_id,
            claim_id=claim_id,
            action=request.action,
            disposition=request.disposition or claim.category,
            reviewer_id=request.reviewer_id,
            notes=request.notes,
            timestamp=timestamp,
        )
        db.add(audit_event)
        db.commit()

        response = ReviewerActionResponse(
            success=True,
            claim_id=claim_id,
            review_state=claim.review_state,
            disposition=request.disposition or claim.category,
            audit_event_id=event_id,
            timestamp=timestamp,
        )

        # Broadcast action event to connected UI clients
        await stream_manager.broadcast("CLAIM_ACTIONED", response.model_dump())

        return response

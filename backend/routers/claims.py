"""Claims REST API endpoints."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.config import settings
from backend.schemas import (
    ClaimInput,
    ClaimRecord,
    ValidationFinding,
    AnomalyEvidence,
    ReviewerActionRequest,
    ReviewerActionResponse,
)
from backend.models import ClaimModel, ValidationFindingModel, AuditEventModel
from backend.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["Claims"])

@router.post("", response_model=ClaimRecord, status_code=201)
async def ingest_claim(claim: ClaimInput, db: Session = Depends(get_db)):
    """Ingest, validate, score, and persist a single claim event."""
    try:
        return await ClaimService.process_claim(claim, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=List[ClaimRecord])
def list_claims(
    limit: int = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None, description="Filter by category: READY, CORRECTION, REVIEW"),
    db: Session = Depends(get_db)
):
    """Retrieve recent claims with findings and anomaly evidence."""
    query = db.query(ClaimModel).order_by(ClaimModel.created_at.desc())
    if category:
        query = query.filter(ClaimModel.category == category.upper())
    
    claims = query.limit(limit).all()
    results = []
    for c in claims:
        # Load findings
        findings = [
            ValidationFinding(
                rule_id=f.rule_id,
                field=f.field,
                message=f.message,
                severity=f.severity,
                passed=f.passed,
            ) for f in c.findings
        ]
        
        # Parse anomaly evidence
        anomaly_evidence = AnomalyEvidence()
        if c.anomaly_evidence_json:
            try:
                anomaly_evidence = AnomalyEvidence(**json.loads(c.anomaly_evidence_json))
            except Exception:
                pass

        results.append(ClaimRecord(
            claim_id=c.claim_id,
            patient_id=c.patient_id,
            provider_id=c.provider_id,
            service_date=c.service_date,
            submission_timestamp=c.submission_timestamp,
            diagnosis_code=c.diagnosis_code,
            procedure_code=c.procedure_code,
            claim_amount=c.claim_amount,
            service_lines_count=c.service_lines_count,
            injected_scenario=c.injected_scenario,
            processing_status=c.processing_status,
            category=c.category,
            triage_score=c.triage_score,
            validation_findings=findings,
            anomaly_evidence=anomaly_evidence,
            execution_target=anomaly_evidence.execution_target or settings.EXECUTION_TARGET,
            latency_p50_ms=anomaly_evidence.latency_p50_ms,
            latency_p95_ms=anomaly_evidence.latency_p95_ms,
            review_state=c.review_state,
            created_at=c.created_at,
        ))
    return results

@router.get("/{claim_id}")
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed claim history including findings, alerts, and audit trail."""
    c = db.query(ClaimModel).filter(ClaimModel.claim_id == claim_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Claim not found")

    findings = [
        ValidationFinding(
            rule_id=f.rule_id,
            field=f.field,
            message=f.message,
            severity=f.severity,
            passed=f.passed,
        ) for f in c.findings
    ]

    anomaly_evidence = AnomalyEvidence()
    if c.anomaly_evidence_json:
        try:
            anomaly_evidence = AnomalyEvidence(**json.loads(c.anomaly_evidence_json))
        except Exception:
            pass

    audit_events = [
        {
            "event_id": a.event_id,
            "action": a.action,
            "disposition": a.disposition,
            "reviewer_id": a.reviewer_id,
            "notes": a.notes,
            "timestamp": a.timestamp,
        } for a in c.audit_events
    ]

    return {
        "claim": ClaimRecord(
            claim_id=c.claim_id,
            patient_id=c.patient_id,
            provider_id=c.provider_id,
            service_date=c.service_date,
            submission_timestamp=c.submission_timestamp,
            diagnosis_code=c.diagnosis_code,
            procedure_code=c.procedure_code,
            claim_amount=c.claim_amount,
            service_lines_count=c.service_lines_count,
            injected_scenario=c.injected_scenario,
            processing_status=c.processing_status,
            category=c.category,
            triage_score=c.triage_score,
            validation_findings=findings,
            anomaly_evidence=anomaly_evidence,
            execution_target=anomaly_evidence.execution_target or settings.EXECUTION_TARGET,
            latency_p50_ms=anomaly_evidence.latency_p50_ms,
            latency_p95_ms=anomaly_evidence.latency_p95_ms,
            review_state=c.review_state,
            created_at=c.created_at,
        ),
        "audit_events": audit_events
    }

@router.post("/{claim_id}/action", response_model=ReviewerActionResponse)
async def reviewer_action(
    claim_id: str,
    action_req: ReviewerActionRequest,
    db: Session = Depends(get_db)
):
    """Record reviewer acknowledgement or final disposition with audit persistence."""
    try:
        return await ClaimService.apply_reviewer_action(claim_id, action_req, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

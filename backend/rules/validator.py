"""Deterministic rule validation engine for incoming claims."""
from datetime import datetime, date, timedelta, timezone
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from backend.schemas import ClaimInput, ValidationFinding
from backend.models import ClaimModel
from backend.config import settings

class ClaimValidator:
    """Evaluates business rules and duplicate keys deterministically."""

    @staticmethod
    def validate_claim(claim: ClaimInput, db: Optional[Session] = None) -> Tuple[List[ValidationFinding], bool, bool]:
        """
        Validates claim fields and duplicate constraints.
        Returns:
            findings: List of ValidationFinding records
            has_error: True if any ERROR severity rule failed
            is_duplicate: True if duplicate match was detected
        """
        findings: List[ValidationFinding] = []
        has_error = False
        is_duplicate = False

        # 1. Missing / Empty Required Fields
        required_fields = [
            ("diagnosis_code", "Diagnosis Code (ICD-10)", "VAL_REQ_DIAG"),
            ("procedure_code", "Procedure Code (CPT/HCPCS)", "VAL_REQ_PROC"),
            ("service_date", "Date of Service", "VAL_REQ_DATE"),
        ]
        for field_name, label, rule_id in required_fields:
            val = getattr(claim, field_name, None)
            if not val or not str(val).strip():
                findings.append(ValidationFinding(
                    rule_id=rule_id,
                    field=field_name,
                    message=f"Missing required field: {label}",
                    severity="ERROR",
                    passed=False
                ))
                has_error = True
            else:
                findings.append(ValidationFinding(
                    rule_id=rule_id,
                    field=field_name,
                    message=f"{label} present",
                    severity="INFO",
                    passed=True
                ))

        # 2. Amount Validation
        if claim.claim_amount is None or claim.claim_amount <= 0:
            findings.append(ValidationFinding(
                rule_id="VAL_INVALID_AMOUNT",
                field="claim_amount",
                message=f"Claim amount must be strictly greater than $0.00 (received ${claim.claim_amount})",
                severity="ERROR",
                passed=False
            ))
            has_error = True
        elif claim.claim_amount > 100000.0:
            # High amount warning
            findings.append(ValidationFinding(
                rule_id="VAL_HIGH_AMOUNT",
                field="claim_amount",
                message=f"Claim amount exceeds standard threshold warning (${claim.claim_amount:,.2f})",
                severity="WARNING",
                passed=True
            ))
        else:
            findings.append(ValidationFinding(
                rule_id="VAL_AMOUNT_OK",
                field="claim_amount",
                message="Claim amount is within standard operational range",
                severity="INFO",
                passed=True
            ))

        # 3. Line Count Check
        if claim.service_lines_count < 1:
            findings.append(ValidationFinding(
                rule_id="VAL_INVALID_LINES",
                field="service_lines_count",
                message="Service line count must be at least 1",
                severity="ERROR",
                passed=False
            ))
            has_error = True

        # 4. Service Date Chronology Check
        parsed_service_date = None
        if claim.service_date:
            try:
                parsed_service_date = datetime.strptime(claim.service_date, "%Y-%m-%d").date()
                today = date.today()
                if parsed_service_date > today:
                    findings.append(ValidationFinding(
                        rule_id="VAL_FUTURE_DATE",
                        field="service_date",
                        message=f"Service date {claim.service_date} cannot be in the future relative to current date {today}",
                        severity="ERROR",
                        passed=False
                    ))
                    has_error = True
            except ValueError:
                findings.append(ValidationFinding(
                    rule_id="VAL_DATE_FORMAT",
                    field="service_date",
                    message="Service date format must be ISO YYYY-MM-DD",
                    severity="ERROR",
                    passed=False
                ))
                has_error = True

        submitted = None
        try:
            submitted = datetime.fromisoformat(claim.submission_timestamp.replace("Z", "+00:00"))
            if submitted.tzinfo is None:
                raise ValueError("timezone required")
            submitted = submitted.astimezone(timezone.utc)
            if parsed_service_date and parsed_service_date > submitted.date():
                raise ValueError("service date is after submission")
        except ValueError:
            findings.append(ValidationFinding(rule_id="VAL_SUBMISSION_DATE", field="submission_timestamp",
                message="Submission must have a valid timezone-aware timestamp on or after the service date",
                severity="ERROR", passed=False))
            has_error = True

        # 5. Duplicate Submission Detection
        # Duplicate key: (patient_id, provider_id, procedure_code, service_date) within window
        if db is not None and not has_error and claim.procedure_code:
            cutoff = submitted - timedelta(days=settings.DUPLICATE_WINDOW_DAYS)

            existing = db.query(ClaimModel).filter(
                ClaimModel.claim_id != claim.claim_id,
                ClaimModel.patient_id == claim.patient_id,
                ClaimModel.provider_id == claim.provider_id,
                ClaimModel.procedure_code == claim.procedure_code,
                ClaimModel.service_date == claim.service_date,
            ).all()
            matches = []
            for prior in existing:
                try:
                    prior_time = datetime.fromisoformat(prior.submission_timestamp.replace("Z", "+00:00"))
                    if prior_time.tzinfo and cutoff <= prior_time.astimezone(timezone.utc) <= submitted:
                        matches.append(prior)
                except ValueError:
                    continue
            existing = matches[0] if matches else None

            if existing:
                is_duplicate = True
                findings.append(ValidationFinding(
                    rule_id="VAL_DUPLICATE_CLAIM",
                    field="claim_id",
                    message=f"Potential duplicate claim detected: matching claim {existing.claim_id} submitted on {existing.submission_timestamp}",
                    severity="WARNING",
                    passed=False
                ))
            else:
                findings.append(ValidationFinding(
                    rule_id="VAL_DUPLICATE_CHECK",
                    field="claim_id",
                    message="No matching prior duplicate found in operational window",
                    severity="INFO",
                    passed=True
                ))

        return findings, has_error, is_duplicate

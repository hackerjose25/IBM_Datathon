import { useState } from 'react'
import { Check, ClipboardList, FileWarning } from 'lucide-react'

const ACTIONS = ['READY', 'CORRECTION', 'REVIEW']

function evidenceLines(evidence) {
  if (evidence == null) return []
  if (Array.isArray(evidence)) return evidence.map((item) => typeof item === 'string' ? item : item && typeof item === 'object' ? item.message || item.description || JSON.stringify(item) : String(item))
  if (typeof evidence === 'object') {
    if (Array.isArray(evidence.factors) && evidence.factors.length > 0) {
      const lines = [...evidence.factors]
      if (evidence.inference_latency_ms != null) {
        lines.push(`Inference latency: ${evidence.inference_latency_ms} ms (${evidence.execution_target || 'LOCAL_MOCK'})`)
      }
      return lines
    }
    return Object.entries(evidence).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${typeof value === 'object' ? JSON.stringify(value) : value}`)
  }
  return [String(evidence)]
}


export default function ClaimDetails({ claim, onReview }) {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  if (!claim) {
    return <aside className="panel detail-panel detail-empty"><ClipboardList size={23} /><h2>Claim details</h2><p>Select a claim from the live feed to inspect its findings and record a disposition.</p></aside>
  }

  const data = claim.claim || {}
  const decision = claim.decision || {}
  const review = claim.review || {}
  const rawFindings = decision.rule_findings || decision.validation_findings || []
  const findings = Array.isArray(rawFindings) ? rawFindings : []
  const anomalyEvidence = decision.anomaly_evidence ?? decision.anomaly ?? null
  const anomalyLines = evidenceLines(anomalyEvidence)
  const anomalyFlagged = decision.anomaly_flagged ?? decision.anomaly?.flagged ?? decision.anomaly?.detected ?? anomalyEvidence?.flagged

  async function submit(disposition) {
    setSaving(true)
    setError('')
    try {
      await onReview(claim.claim_id, disposition)
    } catch (reason) {
      setError(reason.message || 'Could not save reviewer action')
    } finally {
      setSaving(false)
    }
  }

  return (
    <aside className="panel detail-panel">
      <div className="panel-heading detail-title">
        <div><span className="eyebrow">CLAIM DETAILS</span><h2>{claim.claim_id}</h2></div>
        <span className={`badge badge-${((decision.status || '').toLowerCase() === 'error' ? 'error' : decision.category || 'pending').toLowerCase()}`}>{(decision.status || '').toLowerCase() === 'error' ? 'ERROR' : decision.category || 'PENDING'}</span>
      </div>
      <div className="detail-section">
        <h3>Claim information</h3>
        <dl className="detail-grid">
          <div><dt>Provider</dt><dd>{data.provider_id || '—'}</dd></div>
          <div><dt>Patient</dt><dd>{data.patient_id || '—'}</dd></div>
          <div><dt>Service date</dt><dd>{data.service_date || '—'}</dd></div>
          <div><dt>Claim amount</dt><dd>{typeof data.claim_amount === 'number' ? data.claim_amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : '—'}</dd></div>
          <div><dt>Diagnosis codes</dt><dd>{data.diagnosis_codes?.join(', ') || data.diagnosis_code || '—'}</dd></div>
          <div><dt>Procedure codes</dt><dd>{data.procedure_codes?.join(', ') || data.procedure_code || '—'}</dd></div>
        </dl>
      </div>
      <div className="detail-section">
        <div className="section-label"><FileWarning size={15} /><h3>Deterministic validation findings</h3></div>
        {findings.length ? <ul className="findings-list">{findings.map((finding, index) => <li key={`${finding.rule_id || finding.code || finding.rule_code || 'finding'}-${index}`}><strong>{finding.rule_id || finding.code || finding.rule_code || finding.severity || 'Finding'}</strong><span>{finding.message || finding.description || JSON.stringify(finding)}</span></li>)}</ul> : <p className="muted">No validation findings reported.</p>}

      </div>
      <div className="detail-section">
        <div className="section-label"><FileWarning size={15} /><h3>ML anomaly evidence</h3></div>
        <div className="anomaly-line"><span>Anomaly indicator</span><strong>{anomalyEvidence == null && anomalyFlagged == null ? 'Unavailable' : anomalyFlagged == null ? 'Evidence available' : anomalyFlagged ? 'Flagged' : 'Not flagged'}</strong></div>
        {anomalyLines.length ? <ul className="findings-list">{anomalyLines.map((line, index) => <li key={`anomaly-${index}`}><span>{line}</span></li>)}</ul> : <p className="muted">No anomaly evidence reported.</p>}
        <div className="anomaly-line"><span>Triage priority</span><strong>{Number.isFinite(decision.triage_priority) ? `${decision.triage_priority}/100` : 'Unavailable'}</strong></div>
        {decision.recommended_action && <p className="recommendation">{decision.recommended_action}</p>}
        {(decision.status || '').toLowerCase() === 'error' && <p className="error-note">Scoring failed. This claim is not marked READY.</p>}
      </div>
      <div className="detail-section review-section">
        <div className="section-label"><Check size={15} /><h3>Reviewer disposition</h3></div>
        {review.disposition ? <p className="saved-disposition">Saved: <strong>{review.disposition}</strong></p> : <p className="muted">Choose an action to record your decision.</p>}
        <div className="action-buttons">{ACTIONS.map((action) => <button key={action} className={`action-button action-${action.toLowerCase()}`} disabled={saving} onClick={() => submit(action)}>{action}</button>)}</div>
        {error && <p className="error-note">{error}</p>}
      </div>
    </aside>
  )
}

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Activity, ShieldCheck } from 'lucide-react'
import ClaimDetails from './components/ClaimDetails.jsx'
import ClaimTable from './components/ClaimTable.jsx'
import { useClaimsSocket } from './hooks/useClaimsSocket.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const REVIEWER_ID = 'REV-001'

function normalizeScoredEvent(event) {
  const payload = event.data ?? event.payload ?? event.claim ?? event
  const rawClaim = payload.claim ?? payload.claim_data ?? payload
  const decision = payload.decision ?? rawClaim.decision ?? payload.scoring ?? {}
  const statusValue = decision.status ?? payload.status ?? rawClaim.status ?? payload.scoring_status
  const status = typeof statusValue === 'string' ? statusValue.toLowerCase() : 'scored'
  const validationFindings = decision.validation_findings ?? payload.validation_findings ?? rawClaim.validation_findings ?? decision.rule_findings ?? []
  const anomalyEvidence = decision.anomaly_evidence ?? payload.anomaly_evidence ?? rawClaim.anomaly_evidence ?? decision.anomaly ?? null
  return {
    ...rawClaim,
    claim_id: rawClaim.claim_id ?? rawClaim.claimId ?? payload.claim_id ?? payload.claimId ?? event.claim_id,
    claim: rawClaim.claim ?? rawClaim,
    decision: {
      ...decision,
      status,
      category: decision.category ?? payload.category ?? rawClaim.category ?? payload.recommendation ?? null,
      triage_priority: decision.triage_priority ?? payload.triage_priority ?? rawClaim.triage_priority ?? payload.priority_score ?? null,
      rule_findings: Array.isArray(validationFindings) ? validationFindings : [],
      anomaly_evidence: anomalyEvidence,
      anomaly_flagged: decision.anomaly_flagged ?? payload.anomaly_flagged ?? rawClaim.anomaly_flagged ?? decision.anomaly?.flagged ?? (typeof anomalyEvidence === 'boolean' ? anomalyEvidence : anomalyEvidence?.flagged) ?? null,
      anomaly: decision.anomaly ?? (anomalyEvidence != null ? {} : null),
      recommended_action: decision.recommended_action ?? payload.recommended_action ?? rawClaim.recommended_action,
    },
    review: rawClaim.review ?? payload.review ?? { state: 'pending', disposition: null },
  }
}

export default function App() {
  const [claims, setClaims] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [streamError, setStreamError] = useState('')
  const [streamStarting, setStreamStarting] = useState(false)
  const [streamStarted, setStreamStarted] = useState(false)
  const { connection, lastMessageAt } = useClaimsSocket()
  const selectedClaim = useMemo(() => claims.find((claim) => claim.claim_id === selectedId) || null, [claims, selectedId])

  const applyEvent = useCallback((event) => {
    const type = event?.type ?? event?.event_type ?? event?.event
    if (type === 'CLAIM_SCORED' || type === 'claim.upserted') {
      const incoming = normalizeScoredEvent(event)
      if (!incoming.claim_id) return
      setClaims((current) => {
        const index = current.findIndex((claim) => claim.claim_id === incoming.claim_id)
        if (index < 0) return [incoming, ...current]
        const next = [...current]
        next[index] = incoming
        return next
      })
      setSelectedId((current) => current || incoming.claim_id)
    } else if ((type === 'review.updated' || type === 'REVIEW_UPDATED') && event.data?.claim_id) {
      setClaims((current) => current.map((claim) => claim.claim_id === event.data.claim_id ? { ...claim, review: event.data.review } : claim))
    } else if (type === 'stream.error' || type === 'STREAM_ERROR') {
      setStreamError(event.data?.message || 'The claim stream reported an error')
    }
  }, [])

  useEffect(() => {
    const listener = (event) => applyEvent(event.detail)
    window.addEventListener('claimguard:socket-event', listener)
    return () => window.removeEventListener('claimguard:socket-event', listener)
  }, [applyEvent])

  const recordReview = async (claimId, disposition) => {
    const response = await fetch(`${API_URL}/api/claims/${encodeURIComponent(claimId)}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'RESOLVE', disposition, reviewer_id: REVIEWER_ID, notes: 'Reviewed via UI' }),
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || `Request failed (${response.status})`)
    }
    const result = await response.json().catch(() => ({}))
    const updatedReview = result.review || result
    const fallbackReview = { state: 'resolved', disposition, reviewer_id: REVIEWER_ID, updated_at: new Date().toISOString() }
    setClaims((current) => current.map((claim) => claim.claim_id === claimId ? {
      ...claim,
      review: { ...fallbackReview, ...updatedReview, disposition: updatedReview.disposition || disposition },
    } : claim))
  }

  const startStream = async () => {
    setStreamStarting(true)
    setStreamError('')
    try {
      const response = await fetch(`${API_URL}/api/stream/start`, { method: 'POST' })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.detail || `Could not start stream (${response.status})`)
      }
      setStreamStarted(true)
    } catch (error) {
      setStreamError(error.message || 'Could not start synthetic stream')
    } finally {
      setStreamStarting(false)
    }
  }

  const countByCategory = (category) => claims.filter((item) => (item.decision?.status || '').toLowerCase() !== 'error' && item.decision?.category === category).length

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#"><span className="brand-icon"><ShieldCheck size={19} /></span><span>ClaimGuard</span></a>
        <div className="stream-status"><span className={`status-dot status-${connection}`} /><span>{connection === 'connected' ? 'Stream connected' : connection === 'connecting' ? 'Connecting…' : 'Reconnecting…'}</span>{lastMessageAt && <span className="last-event">· event {lastMessageAt.toLocaleTimeString()}</span>}</div>
      </header>
      <section className="page-heading"><div><div className="eyebrow"><Activity size={14} /> REAL-TIME CLAIMS</div><h1>Claims review</h1><p>Review incoming claims and record a human disposition.</p></div><button className="stream-button" onClick={startStream} disabled={streamStarting || streamStarted}>{streamStarting ? 'Starting…' : streamStarted ? 'Synthetic Stream Started' : 'Start Synthetic Stream'}</button></section>
      <section className="summary-row">
        <div className="summary-card"><span>Total claims</span><strong>{claims.length}</strong></div>
        <div className="summary-card"><span>Ready</span><strong>{countByCategory('READY')}</strong></div>
        <div className="summary-card"><span>Correction</span><strong>{countByCategory('CORRECTION')}</strong></div>
        <div className="summary-card"><span>Review</span><strong>{countByCategory('REVIEW')}</strong></div>
      </section>
      {streamError && <div className="stream-error" role="alert">{streamError}<button onClick={() => setStreamError('')}>Dismiss</button></div>}
      <div className="workspace-grid">
        <ClaimTable claims={claims} selectedId={selectedId} onSelect={setSelectedId} />
        <ClaimDetails claim={selectedClaim} onReview={recordReview} />
      </div>
      <footer className="footnote">Triage priority is an operational signal, not a fraud or denial probability. Final disposition remains with the reviewer.</footer>
    </main>
  )
}

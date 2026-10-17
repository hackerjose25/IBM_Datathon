import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Activity, ArrowUpRight, ShieldCheck } from 'lucide-react'
import ClaimDetails from './components/ClaimDetails.jsx'
import ClaimTable from './components/ClaimTable.jsx'
import { useClaimsSocket } from './hooks/useClaimsSocket.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const REVIEWER_ID = 'REV-001'

function normalizeScoredEvent(event) {
  const payload = event.data ?? event.payload ?? event.claim ?? event
  const rawClaim = payload.claim ?? payload.claim_data ?? payload
  const decision = payload.decision ?? rawClaim.decision ?? payload.scoring ?? {}
  const statusValue = decision.status ?? payload.status ?? rawClaim.status ?? payload.scoring_status ?? rawClaim.processing_status
  const status = typeof statusValue === 'string' ? statusValue.toLowerCase() : 'scored'
  const validationFindings = decision.validation_findings ?? payload.validation_findings ?? rawClaim.validation_findings ?? decision.rule_findings ?? []
  const anomalyEvidence = decision.anomaly_evidence ?? payload.anomaly_evidence ?? rawClaim.anomaly_evidence ?? decision.anomaly ?? null
  const triageScore = decision.triage_priority ?? payload.triage_priority ?? rawClaim.triage_priority ?? payload.triage_score ?? payload.priority_score ?? null
  return {
    ...rawClaim,
    claim_id: rawClaim.claim_id ?? rawClaim.claimId ?? payload.claim_id ?? payload.claimId ?? event.claim_id,
    claim: rawClaim.claim ?? rawClaim,
    decision: {
      ...decision,
      status,
      category: decision.category ?? payload.category ?? rawClaim.category ?? payload.recommendation ?? null,
      triage_priority: triageScore != null ? Number(triageScore) : null,
      rule_findings: Array.isArray(validationFindings) ? validationFindings : [],
      anomaly_evidence: anomalyEvidence,
      anomaly_flagged: decision.anomaly_flagged ?? payload.anomaly_flagged ?? rawClaim.anomaly_flagged ?? decision.anomaly?.flagged ?? (typeof anomalyEvidence === 'boolean' ? anomalyEvidence : anomalyEvidence?.is_anomaly ?? anomalyEvidence?.flagged) ?? null,
      anomaly: decision.anomaly ?? (anomalyEvidence != null ? {} : null),
      recommended_action: decision.recommended_action ?? payload.recommended_action ?? rawClaim.recommended_action,
    },
    review: rawClaim.review ?? payload.review ?? {
      state: (rawClaim.review_state || 'pending').toLowerCase(),
      disposition: rawClaim.reviewer_decision?.decision || null,
    },
  }
}

export default function App() {
  const [view, setView] = useState(() => window.location.hash === '#dashboard' ? 'dashboard' : 'landing')
  const videoRef = useRef(null)
  useEffect(() => {
    const syncView = () => setView(window.location.hash === '#dashboard' ? 'dashboard' : 'landing')
    window.addEventListener('hashchange', syncView)
    return () => window.removeEventListener('hashchange', syncView)
  }, [])
  useEffect(() => {
    window.scrollTo(0, 0)
    if (view !== 'landing') return
    const video = videoRef.current
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const sync = () => {
      if (!video) return
      if (preference.matches) { video.pause(); video.currentTime = 0 }
      else video.play().catch(() => {})
    }
    preference.addEventListener('change', sync)
    sync()
    return () => preference.removeEventListener('change', sync)
  }, [view])
  const [claims, setClaims] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [streamError, setStreamError] = useState('')
  const [streamStarting, setStreamStarting] = useState(false)
  const [streamStarted, setStreamStarted] = useState(false)
  const { connection, lastMessageAt } = useClaimsSocket()
  const selectedClaim = useMemo(() => claims.find((claim) => claim.claim_id === selectedId) || null, [claims, selectedId])

  // Load existing claims on initial mount
  useEffect(() => {
    fetch(`${API_URL}/api/claims?limit=500`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const normalized = data.map((c) => normalizeScoredEvent({ event: 'CLAIM_SCORED', data: c }))
          setClaims(normalized)
          setSelectedId((current) => current || normalized[0]?.claim_id)
        }
      })
      .catch((err) => console.warn('Could not load initial claims:', err))
  }, [])

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
    } else if ((type === 'review.updated' || type === 'REVIEW_UPDATED' || type === 'CLAIM_ACTIONED') && event.data?.claim_id) {
      const updatedReview = event.data.review ?? {
        state: (event.data.review_state || 'resolved').toLowerCase(),
        disposition: event.data.disposition,
        reviewer_id: event.data.reviewer_id,
      }
      setClaims((current) => current.map((claim) => (claim.claim_id === event.data.claim_id ? { ...claim, review: updatedReview } : claim)))
    } else if (type === 'STREAM_METRICS' && event.data?.status === 'completed') {
      setStreamStarted(false)
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

  if (view === 'landing') return (
    <main className="landing-shell">
      <video ref={videoRef} className="landing-video" muted loop playsInline preload="auto" aria-hidden="true" disablePictureInPicture
        poster="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260912_105822_bf7c2d53-9957-4521-bbbf-7c1ab7a70130.png"
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260912_105953_21ad8049-9088-4a00-bad3-aee6b5575a2b.mp4" />
      <header className="landing-header">
        <a className="brand" href="#"><span className="brand-icon"><ShieldCheck size={24} aria-hidden="true" /></span><span>ClaimGuard</span></a>
        <nav className="landing-nav" aria-label="Main navigation"><span>Claims intelligence</span><span className="nav-divider" /><a href="#dashboard">Dashboard <ArrowUpRight size={14} aria-hidden="true" /></a></nav>
        <a className="stream-button landing-cta" href="#dashboard"><span>Open dashboard</span><span className="button-knob"><ArrowUpRight size={20} aria-hidden="true" /></span></a>
      </header>
      <section className="landing-content">
        <div className="hero-copy"><div className="eyebrow">YOUR PRE-SUBMISSION CHECKPOINT</div><h1><span>Clearer claims.</span><span>Confident decisions.</span></h1><p><span className="tag-icon"><ShieldCheck size={20} aria-hidden="true" /></span>Understand the evidence. Keep the human decision.</p></div>
        <aside className="hero-panel"><div className="hero-panel-top"><span>AI-assisted <i className="landing-live-dot" /></span><ShieldCheck size={35} aria-hidden="true" /></div><p>Deterministic checks.<br />Anomaly evidence.<br />Human oversight.</p><div className="category-legend"><span>Ready</span><span>Correction</span><span>Review</span></div><div className="category-track" aria-hidden="true"><i /><i /><i /></div></aside>
      </section>
      <footer className="landing-footer"><div className="landing-principles"><div><strong>03</strong><span>Clear recommendation<br />categories</span></div><span className="principle-divider" /><div><strong>01</strong><span>Human reviewer.<br />Final decision.</span></div></div><a className="meet-workspace" href="#dashboard"><span className="sphere-thumb" aria-hidden="true" /><span>Enter the workspace</span><span className="button-knob"><ArrowUpRight size={19} aria-hidden="true" /></span></a></footer>
      <span className="landing-disclaimer">SYNTHETIC CLAIMS ONLY · TRIAGE PRIORITY IS NOT A FRAUD PROBABILITY</span>
    </main>
  )

  return (
    <main className="app-shell">
      <div className="background-plate" aria-hidden="true" />
      <header className="topbar">
        <a className="brand" href="#"><span className="brand-icon"><ShieldCheck size={19} /></span><span>ClaimGuard</span></a><a className="back-home" href="#">Back to home</a>
        <div className="stream-status"><span className={`status-dot status-${connection}`} /><span>{connection === 'connected' ? 'Stream connected' : connection === 'connecting' ? 'Connecting…' : 'Reconnecting…'}</span>{lastMessageAt && <span className="last-event">· event {lastMessageAt.toLocaleTimeString()}</span>}</div>
      </header>
      <section className="page-heading">
        <div className="hero-copy"><div className="eyebrow"><Activity size={14} /> LIVE CLAIMS WORKSPACE</div><h1>Claims review</h1><p>Inspect the evidence and record a human disposition.</p></div><button className="stream-button" onClick={startStream} disabled={streamStarting || streamStarted}><span>{streamStarting ? 'Starting…' : streamStarted ? 'Synthetic Stream Started' : 'Start Synthetic Stream'}</span><span className="button-knob"><ArrowUpRight size={20} aria-hidden="true" /></span></button>
      </section>
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

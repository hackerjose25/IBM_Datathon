import { ArrowDownUp } from 'lucide-react'

function CategoryBadge({ decision }) {
  const category = decision?.status?.toLowerCase() === 'error' ? 'ERROR' : decision?.category || 'PENDING'
  return <span className={`badge badge-${category.toLowerCase()}`}>{category}</span>
}

export default function ClaimTable({ claims, selectedId, onSelect }) {
  return (
    <section className="panel overflow-hidden">
      <div className="panel-heading">
        <div>
          <h2>Live claims</h2>
          <p>Incoming synthetic claim events</p>
        </div>
        <span className="count-pill">{claims.length} total</span>
      </div>
      <div className="overflow-x-auto">
        <table className="claim-table">
          <thead>
            <tr>
              <th>Claim <ArrowDownUp size={13} /></th>
              <th>Provider</th>
              <th>Service date</th>
              <th>Amount</th>
              <th>Priority</th>
              <th>Recommendation</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((item) => {
              const claim = item.claim || {}
              const decision = item.decision || {}
              return (
                <tr key={item.claim_id} onClick={() => onSelect(item.claim_id)} className={selectedId === item.claim_id ? 'selected-row' : ''}>
                  <td className="claim-id">{item.claim_id}</td>
                  <td>{claim.provider_id || '—'}</td>
                  <td>{claim.service_date || '—'}</td>
                  <td>{typeof claim.claim_amount === 'number' ? claim.claim_amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : '—'}</td>
                  <td>{Number.isFinite(decision.triage_priority) ? `${decision.triage_priority}/100` : '—'}</td>
                  <td><CategoryBadge decision={decision} /></td>
                </tr>
              )
            })}
            {claims.length === 0 && <tr><td colSpan="6" className="empty-row">Waiting for claim events…</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  )
}

# ClaimGuard

**Real-Time AI Healthcare Claims Risk Intelligence**  
Team Bug Eaters | IBM Z Datathon 2026 | Track 01: Real-Time AI for Critical Decisions

ClaimGuard is a proposed AI-assisted checkpoint for healthcare insurance claims before onward submission. It combines deterministic validation with machine-learning anomaly detection to identify potential issues, explain the evidence, and recommend correction or human review while each transaction is processed.

> Status: local prototype verified on Windows AMD64 using synthetic claims, saved Isolation Forest inference, WebSocket delivery, reviewer persistence and audit records. LinuxONE deployment is now verified on the event-provided Ubuntu s390x VM; remote tests and measurements are in evidence/linuxone/. The original proposal is `IBM datathon.pdf`, prepared 14 October 2026; local results do not establish real-world fraud performance or complete the IBM deployment gate.

## Problem and users

Missing fields, inconsistent information, unusual billing patterns, and duplicate submissions can cause delays and administrative rework. ClaimGuard targets hospital revenue-cycle teams, claims operations staff, and claims reviewers who need actionable evidence before a claim moves downstream.

## MVP scope

- Stream synthetic JSON/CSV claim events at a configurable interval.
- Validate required values, dates, amounts, duplicate keys, and incompatible values.
- Engineer claim and historical-context features and run a trained Isolation Forest model.
- Execute core inference on an IBM LinuxONE virtual machine.
- Display incoming claims, rule findings, anomaly indicators, priority, recommended actions, and latency in a live dashboard.
- Let reviewers acknowledge or resolve alerts and record dispositions in an audit trail.

### Decision categories

| Category | Meaning | Recommended action |
| --- | --- | --- |
| READY | Required checks pass and no notable anomaly is detected | Continue processing |
| CORRECTION | Deterministic validation identifies a fixable issue | Return for correction |
| REVIEW | An unusual pattern or possible duplicate requires investigation | Hold for human review |

A 0–100 triage index expresses review priority. It is **not a calibrated fraud or denial probability**. An anomaly is not proof of fraud. Routing precedence is: scoring failure → ERROR processing state with REVIEW recommendation; otherwise validation error → CORRECTION; otherwise duplicate, model anomaly, or normalized signal ≥60 → REVIEW; otherwise READY. Triage uses a floor of 55 for correction, 70 for review, a cap of 25 for ready, and 100 for scoring failures. These are operational heuristics, not calibrated probabilities.

## Proposed processing flow

1. Receive a synthetic claim event.
2. Run structural and business-rule validation.
3. Compute features using information available at decision time.
4. Score the claim with the trained model on LinuxONE.
5. Combine validation findings, the anomaly signal, and business priorities into a recommendation.
6. Publish live updates through WebSockets and persist claims, alerts, and reviewer actions.

The web interface may be hosted separately. The inference endpoint must actually execute on LinuxONE for the IBM-hosted demonstration.

## Proposed technology stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| Dashboard | React, Vite, Tailwind CSS | Claims table, details, alerts, reviewer actions |
| Charts | Recharts | Trends and risk breakdowns |
| API and rules | Python, FastAPI | Ingestion, validation, inference orchestration |
| Live events | WebSockets | Claim and alert updates |
| ML and data | scikit-learn, Pandas, NumPy | Feature processing and Isolation Forest |
| Storage | SQLite | Prototype claims, alerts, review actions |
| Deployment | IBM LinuxONE VM | Inference and API service |
| Collaboration | GitHub, SSH; optional Docker | Versioning and deployment |

## Data and model strategy

Use synthetic data only. The proposal identifies CMS Synthetic Medicare Claims for historical-style structures and amounts, Synthea for generated records, and injected scenarios for controlled tests. Dataset availability, exact versions, mappings, and usage terms still need to be checked during implementation.

Candidate features include claim amount, service-line count, provider-level amount deviation, repeated submissions within a defined window, age of claim, and contextual frequency. Use consistent categorical encoding and missing-value handling between training and inference. Exclude future outcomes from decision-time features.

Train an unsupervised Isolation Forest baseline. Keep deterministic findings, normalized anomaly signals, and business-priority contributions visible separately. Do not assume synthetic claims datasets contain fraud labels; label injected duplicates, missing fields, and high amounts as simulated scenarios.

## Implementation plan

The source proposes a build window of **17–18 October 2026**. The phases below are planned, not completed milestones.

| Phase | Work | Definition of done |
| --- | --- | --- |
| 1. Data and ML | Prepare synthetic data, inject scenarios, train baseline | Saved model produces repeatable scores for test claims |
| 2. Backend and IBM | Build ingestion/scoring APIs and rules; deploy to LinuxONE | End-to-end request reaches IBM-hosted inference |
| 3. UI and streaming | Build live table, claim detail, alerts, review actions | Incoming claims appear without manual refresh |
| 4. QA and demo | Test routes, measure latency, document limits, record demo | Reproducible showcase and submission assets |

### Team responsibilities

| Role | Proposal owner | Deliverable |
| --- | --- | --- |
| AI / data | Member 1 | Data, features, model evaluation |
| Backend / events | Member 2 | API, simulator, validation, WebSockets |
| Frontend / UX | Member 3 | Dashboard and claim-detail experience |
| IBM platform | Member 4 | LinuxONE deployment, SSH, latency evidence |
| QA / submission | Member 5 | Scenario tests, results, README, deck, demo |

Names were not supplied in the proposal; the member labels are placeholders.

## Getting started

### Environment setup & configuration

ClaimGuard supports dual execution profiles configured via [`.env`](file:///home/dani/Projects/clg/IBM_Datathon/.env) (templated in [`.env.example`](file:///home/dani/Projects/clg/IBM_Datathon/.env.example)):
- **`LOCAL_MOCK`**: Local development, mock testing, and component verification.
- **`IBM_LINUXONE`**: Deployment to IBM LinuxONE (s390x) virtual machines with genuine ML execution.

```bash
# 1. Python Virtual Environment Setup (s390x and x86_64 compatible)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Pre-trained Model Artifact
# Ensure the versioned pre-trained Isolation Forest artifact exists (or generate it)
python -m backend.ml.train

# 3. Run Backend Server (FastAPI + WebSockets)
PYTHONPATH=. uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Run Test Suite
pytest -v
```

### Frontend starter

The initial dashboard lives at the repository root and uses React, Vite, and Tailwind CSS. It requires Node.js 20.19+ or 22.12+. Run `npm install`, then `npm run dev` from the repository root. Configure `VITE_WS_URL` (default `ws://localhost:8000/ws/claims`) and `VITE_API_URL` (default `http://localhost:8000`) in a local `.env` file when the backend uses different addresses. Do not commit secrets in environment files.

The dashboard starts empty and adds or replaces claims as it receives WebSocket events. Click **Start Synthetic Stream** to call `POST /api/stream/start`. Reviewer buttons call `POST /api/claims/{claim_id}/action` with `action: "RESOLVE"`, the selected disposition (`READY`, `CORRECTION`, or `REVIEW`), `reviewer_id: "REV-001"`, and UI notes. The frontend expects a successful JSON response containing either a `review` object or the review object itself.

The backend allows local frontend origins on ports 5173 and 5174 (plus the existing port 3000 origins). The current local dashboard can therefore connect when Vite selects port 5174.

### Dashboard theme

The app opens with a separate animated landing screen, using the supplied looping sphere video, entrance animations, and floating glass navigation. Open dashboard or Enter the workspace navigates to #dashboard; Start Synthetic Stream is available only inside that workspace. Returning home preserves in-memory claims and stream state. Reduced-motion preferences pause the video and disable entrance animation. The dashboard retains live totals and translucent claims panels. Streaming, claim selection, findings, and reviewer dispositions retain their existing API behavior. The page scrolls on smaller screens to keep all review controls accessible. The decorative sphere video and fallback poster are hosted on CloudFront and Inter loads from Google Fonts; local colors and system fonts remain available if those resources cannot load. No additional product controls were added.

### Initial frontend API and event contract (v1)

The frontend connects to `ws://localhost:8000/ws/claims` by default. It handles `CLAIM_SCORED` events (claim fields may be in `data` or nested under `data.claim`), `claim.upserted`, review updates, and stream errors. Scored claim events are replaced by stable `claim_id`. The client reconnects with exponential backoff.

Normalized claims use stable `claim_id`, `received_at`, `updated_at`, and nested objects:

- `claim`: synthetic `patient_id`, `provider_id`, ISO `service_date`, numeric `claim_amount`, and optional `diagnosis_codes`, `procedure_codes`, `place_of_service`.
- `decision`: `category` (`READY`, `CORRECTION`, or `REVIEW`), `status` (`pending`, `scored`, or `error`), integer `triage_priority` from 0–100 when available, deterministic `validation_findings`, ML `anomaly_evidence`, and optional `recommended_action`.
- `review`: `state` (`pending`, `in_progress`, or `resolved`), nullable `disposition` (`READY`, `CORRECTION`, or `REVIEW`), nullable `reviewer_id`, and nullable `updated_at`.

When `decision.status` is `error` (including backend `ERROR` status), the UI shows an ERROR badge and excludes the claim from the READY count. Deterministic `validation_findings` and ML `anomaly_evidence` are shown in separate detail sections. The triage index is an operational priority, not a calibrated fraud or denial probability.

## Evaluation and acceptance checklist

- [x] Synthetic claims continuously enter the local application (100-event live verification).
- [x] Deterministic rules and saved trained inference both run locally; the same workflow also passed on LinuxONE.
- [x] Provisioning context, SSH architecture checks, target tests, service logs and live scoring establish LinuxONE execution (evidence/linuxone/).
- [ ] The dashboard displays findings, anomaly indicators, and suggested actions.
- [x] Backend reviewer acknowledgement and resolution are persisted and auditable; saved resolution survives browser reload.
- [ ] Precision and recall are reported for documented injected scenarios only.
- [ ] False positives and review rates are recorded on held-out synthetic normal data.
- [ ] Patient/provider and time separation are considered where feasible to reduce leakage.
- [ ] Mean, median, and p95 inference latency and stream throughput are measured under a documented load.
- [ ] Dataset realism, label scarcity, calibration, and bias limitations are documented.

Local measurements and workload conditions are recorded in [docs/SUBMISSION.md](docs/SUBMISSION.md) and [evidence/local-verification.json](evidence/local-verification.json). LinuxONE measurements are in [evidence/linuxone/linuxone-verification.json](evidence/linuxone/linuxone-verification.json): scoring-path mean 2.679 ms, median 2.189 ms, p95 2.582 ms; loopback HTTP mean 11.953 ms, median 10.897 ms, p95 17.374 ms (100 serial requests). These exclude internet/tunnel latency. The source's CLM-1042 priority of 87/100 and example amounts of $1,200 and $18,500 are illustrative, not measured outcomes.

## Verified model and workflow contract

- Tested ML versions: scikit-learn 1.8.0, NumPy 2.3.2, Joblib 1.5.3; pinned in both dependency files. Python 3.13.6 was used locally. Python 3.11+ is required for this scikit-learn version. The Windows pins have no matching scikit-learn binary wheel on this s390x VM. The verified target uses Ubuntu scientific packages and requirements-linuxone-api.txt, with a separately trained compatible artifact; see docs/LINUXONE.md.
- Retrain with `python -m backend.ml.train`. The saved artifact records runtime versions, seed 42, generator settings, ordered feature names and preprocessing version. The loader rejects incompatible scikit-learn or feature contracts. The LinuxONE profile requires a disk artifact; only local development may use a clearly labelled in-memory fallback when the artifact is missing.
- Ordered features: log1p(max(0, amount)), max(1, line count), CRC32 provider bucket modulo 100, CRC32 procedure bucket modulo 50 (missing procedure becomes NONE). Training draws synthetic feature vectors; it does not establish realism. The scenario label is not used for inference.
- Duplicate matching uses patient, provider, procedure and service date within 30 days before the incoming submission timestamp, excluding later submissions. Existing claim IDs are rejected as replays without changing review or audit history. Invalid submission chronology is a deterministic error. Missing required identifiers are rejected with HTTP 422.
- Model recommendations remain separate from reviewer dispositions. The latest saved RESOLVE audit event supplies reviewer details in list/detail responses, so the browser restores the saved disposition on reload. Scoring exceptions persist ERROR and cannot appear as READY.
- The synthetic stream uses seed 42 and a unique run ID to avoid claim-ID collisions after restart. Timestamps and identifiers vary across runs. The dashboard loads up to 500 claims and permits another stream after receiving completion.
- Run `python -m pytest -q` for backend checks. Run `python -m scripts.verify_demo` against the running backend for the documented local benchmark, actual 100-event stream and persisted verification review. This writes synthetic test data to the configured database.
- See [LinuxONE access/deployment](docs/LINUXONE.md) and [submission/demo preparation](docs/SUBMISSION.md). LinuxONE execution evidence is now captured in evidence/linuxone/; the final recorded presentation and official submission remain outstanding.

## IBM deployment evidence

Obtain access through the official event setup process. Confirm SSH access and VM architecture, install compatible dependencies, and use s390x-compatible containers if containers are chosen. Capture service logs, a terminal demonstration, and actual request latency.

IBM LinuxONE (Linux on IBM Z, commonly s390x) is distinct from IBM Machine Learning for z/OS. Do not describe the prototype as commercial z/OS transactional inference unless that specific platform is supplied and verified.

## Two-minute demo

| Time | Demonstration |
| --- | --- |
| 0:00–0:20 | Explain the cost of finding claim issues late |
| 0:20–0:50 | Start a synthetic stream of 100 claims and show live arrivals |
| 0:50–1:20 | Inject an unusual claim and explain rules and anomaly indicators |
| 1:20–1:40 | Inspect an alert and record a human review decision |
| 1:40–2:00 | Show the running LinuxONE service, actual latency, and architecture |

## Boundaries and stretch goals

The prototype is not an insurer-grade fraud detector, an automated denial authority, an adjudication engine, or a full HIPAA/X12 production gateway. It must not process identifiable patient records or submit real claims to insurers.

After the MVP is stable, consider a limited X12 837P adapter, feature-level explanations, adaptive prioritization, drift indicators, and richer workflow history. An X12 extension must document its supported field subset; the proposal mentions CLM, NM1, HI, DTP, and SV1 segment families.

## Project documentation

- [HISTORY.md](HISTORY.md): documented planning history, decisions, and future change-log guidance.
- [AGENTS.md](AGENTS.md): instructions for coding assistants working on this project.

## Source and licensing

Source: `IBM datathon.pdf`, *ClaimGuard: Real-Time AI Healthcare Claims Risk Intelligence*, Team Bug Eaters, 14 October 2026, pages 1–8. The document is a hackathon concept proposal; its technical design and results remain proposed until validated in the event environment.

The source names IBM AI on IBM Z, IBM Machine Learning for z/OS, CMS Synthetic Medicare Claims, Synthea, and a LinuxONE ML lab as references, without concrete URLs in the extracted text. No repository license was supplied; licensing remains to be decided by the team.

Public HTTPS hosting preparation and the pending network-exposure approval are documented in [docs/PUBLIC-HOSTING.md](docs/PUBLIC-HOSTING.md). The Sites registration is not a deployed public website yet.

Frontend production URL: [ClaimGuard on Vercel](https://claimguard-dun.vercel.app). The public landing page and direct LinuxONE HTTPS/WSS dashboard connection are verified, including a 100-claim stream and saved review after reload. No local tunnel is required. Automatic API startup, process recovery and restoration of the approved web ports are enabled. Process-failure recovery was tested; a full VM reboot was not. See the hosting guide. See [public hosting status](docs/PUBLIC-HOSTING.md).

# ClaimGuard History

## 2026-10-17 14:11 +05:30 — Backend frontend integration

- Changed: Set the WebSocket default to `ws://localhost:8000/ws/claims` while preserving the `VITE_WS_URL` override; added handling for `CLAIM_SCORED` events and claim upserts.
- Changed: Reviewer actions now POST to `/api/claims/{claim_id}/action` with `action: RESOLVE`, the selected disposition, reviewer `REV-001`, and the UI notes. Added the Start Synthetic Stream button which POSTs to `/api/stream/start`.
- Changed: Claim details render deterministic validation findings and ML anomaly evidence separately. Backend `ERROR` statuses render as ERROR and are excluded from the READY count. Updated README integration instructions.
- Validation/evidence: Production build succeeded with a Node compatibility shim for this sandbox's blocked native `realpathSync`; `git diff --check` passed. `http://127.0.0.1:8000/openapi.json` returned ECONNREFUSED and backend source is absent from this checkout, so live endpoint/WebSocket behavior could not be confirmed. Re-ran `npm install --force` to restore an incomplete local `lucide-react` install (0 reported vulnerabilities).
- Remaining limitations: `npm run build` itself hits sandbox EPERM in Vite's Windows native `realpathSync`; the equivalent Vite build completed using the compatibility shim. End-to-end behavior still depends on the backend being reachable and honoring the supplied contract.

## 2026-10-17 13:32 +05:30 — Minimal frontend and streaming contract

- Changed: Added a React/Vite/Tailwind dashboard with a live claims table, claim detail panel, rule/anomaly/priority presentation, READY/CORRECTION/REVIEW reviewer actions, connection status, and reconnecting WebSocket client. Added package scripts, a Node.js engine constraint, ignored generated/local files, and an npm lockfile.
- Changed: Added `VITE_WS_URL` and `VITE_API_URL` configuration defaults, the proposed v1 WebSocket event and normalized claim contract, and local frontend startup instructions to README.md.
- Decision: The feed begins empty and consumes full-claim `claim.upserted` events, replacing rows by stable `claim_id`. Reviewer actions post a disposition to `/api/claims/{claim_id}/review`. Both are proposed integration points pending backend confirmation.
- Validation/evidence: `npm install` completed successfully (79 packages added, 0 reported vulnerabilities); `git diff --check` passed. No tests or production build were run.
- Remaining limitations: Backend endpoints, WebSocket server, review persistence, and CORS configuration do not exist yet. The production build and UI behavior have not been verified against a running backend.

This file records source-backed planning decisions and subsequent verified changes. It is not a reconstructed Git history. The supplied proposal contains no commit log, release history, deployment evidence, or completed test results.

## 2026-10-17 — Live Uvicorn backend server launch & CORS verification

- Changed:
  - Verified and refined CORS configuration in [`backend/config.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/config.py) to explicitly allow `http://localhost:5173` and `http://127.0.0.1:5173` for the Vite frontend development server.
  - Launched live development server on `http://127.0.0.1:8000` with hot-reload enabled (`uvicorn backend.main:app --reload --port 8000`).
  - Verified clean database schema initialization for `claimguard.db` during lifespan startup.
- Reason: Provide live HTTP REST and WebSocket streaming endpoints to Developer 1's frontend.
- Validation/evidence:
  - Verified `/health` returned HTTP 200 with `status: HEALTHY` and `database: claimguard.db`.
  - Tested live claim ingestion with `POST /api/claims`, returning `201 Created` with validation findings and Isolation Forest anomaly inference.
- Remaining limitations: Running with `EXECUTION_TARGET=LOCAL_MOCK` in local development environment.

## 2026-10-17 — Backend & Ingestion Engine implementation (Developer 2)

- Changed:
  - Created [`.gitignore`](file:///home/dani/Projects/clg/IBM_Datathon/.gitignore) ignoring virtual environments, SQLite databases, and test caches.
  - Implemented [`backend/requirements.txt`](file:///home/dani/Projects/clg/IBM_Datathon/backend/requirements.txt) and [`backend/config.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/config.py) with environment flags (`EXECUTION_TARGET`, `DATABASE_URL`, `DUPLICATE_WINDOW_DAYS`, `ANOMALY_THRESHOLD_SCORE`).
  - Defined database models in [`backend/database.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/database.py) and [`backend/models.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/models.py) using SQLAlchemy: `claims`, `validation_findings`, `alerts`, and `audit_trail`.
  - Built JSON schema contract in [`backend/schemas.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/schemas.py) (`ClaimInput`, `ClaimRecord`, `ValidationFinding`, `AnomalyEvidence`, `ReviewerActionRequest`, `ReviewerActionResponse`, `WebSocketEnvelope`).
  - Implemented deterministic validator in [`backend/rules/validator.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/rules/validator.py) covering missing fields, amount checks, line item counts, date validity, and duplicate submission checks within a configurable window.
  - Implemented baseline ML Isolation Forest scoring and latency tracking in [`backend/ml/inference.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/ml/inference.py) with feature extraction (`log_amount`, `lines`, `provider_hash`, `procedure_hash`) and `LOCAL_MOCK` / `IBM_LINUXONE` target reporting.
  - Built orchestration and event services: [`backend/services/stream_manager.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/services/stream_manager.py) (WebSocket connection & broadcast manager), [`backend/services/claim_service.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/services/claim_service.py) (end-to-end pipeline, priority score scaling, category routing, and audit events), and [`backend/services/generator.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/services/generator.py) (synthetic streaming generator).
  - Built FastAPI application and endpoints in [`backend/main.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/main.py), [`backend/routers/claims.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/routers/claims.py), and [`backend/routers/stream.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/routers/stream.py):
    - `POST /api/claims` (ingest single claim)
    - `GET /api/claims` (query recent claims with optional category filtering)
    - `GET /api/claims/{claim_id}` (claim detail with findings and audit trail)
    - `POST /api/claims/{claim_id}/action` (reviewer acknowledgement / resolution disposition)
    - `POST /api/stream/start`, `POST /api/stream/stop`, `GET /api/stream/status` (synthetic claim generator controls)
    - `/ws/claims` (real-time WebSocket feed)
    - `GET /health` (system and execution target health status)
  - Created comprehensive test suite in [`tests/test_validator.py`](file:///home/dani/Projects/clg/IBM_Datathon/tests/test_validator.py), [`tests/test_inference.py`](file:///home/dani/Projects/clg/IBM_Datathon/tests/test_inference.py), [`tests/test_api.py`](file:///home/dani/Projects/clg/IBM_Datathon/tests/test_api.py), and [`tests/test_stream.py`](file:///home/dani/Projects/clg/IBM_Datathon/tests/test_stream.py).
- Reason: Establish Developer 2 backend capabilities to support real-time claims ingestion, deterministic rule validation, mock ML inference, and WebSocket streaming without blocking Developer 1 (Frontend).
- Validation/evidence: 15 out of 15 automated pytest tests passing (`pytest -v`), plus end-to-end SQLite smoke test verifying persistence of processed claims and audit log entries.
- Remaining limitations: ML model uses synthetic cold-start Isolation Forest baseline; deployment to physical IBM LinuxONE (s390x) VM remains planned for Phase 2/3.

## 2026-10-17 — Schema contract and multi-agent development alignment

- Changed: Defined canonical JSON schemas for claims, validation findings, anomaly evidence, reviewer disposition actions, and WebSocket broadcast events. Established parallel development boundaries for Developer 1 (Frontend / Live UI) and Developer 2 (Backend / Ingestion & Inference).
- Reason: Enable concurrent frontend and backend construction without breaking changes, satisfying AGENTS.md requirements for stable identifiers, explicit error states, separate deterministic vs anomaly findings, and non-negotiable human-in-the-loop audit trails.
- Validation/evidence: Schemas checked against specifications in `AGENTS.md` and `README.md`.
- Remaining limitations: Schema contracts are defined conceptually; code implementations in Pydantic / TypeScript types are pending developer assignment.

## 2026-10-17 — Initial documentation package

Prepared README.md, HISTORY.md, and AGENTS.md from `IBM datathon.pdf` at the user's request.

- Captured the proposed product, architecture, team roles, implementation phases, evaluation plan, and demo sequence.
- Distinguished planned capabilities from verified implementation.
- Added implementation guidance for coding assistants and explicit reminders to preserve human review and synthetic-data boundaries.

This entry records documentation creation only. It does not establish that the application has been built or deployed.

## 2026-10-14 — Concept proposal prepared

The source document identifies Team Bug Eaters and the project ClaimGuard for IBM Z Datathon 2026, Track 01: Real-Time AI for Critical Decisions.

### Decisions recorded in the proposal

| Area | Planned decision | Source |
| --- | --- | --- |
| Product | Pre-submission claims risk checkpoint with human oversight | Pages 1–3 |
| Initial input | Synthetic JSON/CSV claims; X12 837P as an extension | Pages 1, 4 |
| Decision categories | READY, CORRECTION, REVIEW | Page 4 |
| Model | Unsupervised Isolation Forest with engineered claim features | Page 5 |
| Explanations | Separate rule findings, anomaly signals, and review priority | Pages 4–5 |
| Deployment | Run core inference on IBM LinuxONE | Page 6 |
| Stack | React/Vite/Tailwind, FastAPI, WebSockets, scikit-learn, SQLite | Page 6 |
| Delivery | Four build phases and five role assignments | Page 7 |
| Demo | Synthetic stream, unusual claim, reviewer decision, IBM evidence | Page 8 |

### Boundaries established

- Use synthetic data; do not use identifiable patient records or insurer credentials.
- Recommend actions without automatic fraud findings or claim denials.
- Do not represent the 0–100 priority index as a calibrated fraud or denial probability.
- Do not equate LinuxONE deployment with IBM Machine Learning for z/OS.
- Report results on injected scenarios as synthetic test performance only.

## Planned milestones — 2026-10-17 to 2026-10-18

These dates are the proposal's build window, not completion dates.

| Phase | Completion evidence required | Status supported by supplied material |
| --- | --- | --- |
| Data and ML | Versioned data/preprocessing and repeatable saved-model scores | Planned; unverified |
| Backend and IBM | End-to-end request and IBM-hosted inference logs | Planned; unverified |
| UI and streaming | Live arrivals and functioning reviewer actions | Planned; unverified |
| QA and demo | Scenario results, measured latency, reproducible showcase | Planned; unverified |

## Open decisions

- Canonical claim fields, types, validation rules, and duplicate-window semantics.
- API contracts, WebSocket event format, error handling, and review state transitions.
- Score normalization, component weights, thresholds, and category precedence.
- Dataset versions, generation seeds, train/evaluation splits, and model artifact format.
- Dependency versions, repository structure, deployment configuration, and run commands.
- Actual team member names, repository license, and confirmed event-environment details.

These are gaps to resolve during implementation, not additional requirements claimed to come from the proposal.

## Maintaining this history

Add new dated entries above older entries after work is performed. Record what changed, why, the evidence or validation performed, and remaining limitations. Link commits, issues, artifacts, or test reports when available. Keep proposals explicitly labeled as planned; never invent release versions, benchmark results, or completion dates.

Suggested future entry structure:

```markdown
## YYYY-MM-DD — Short change title

- Changed:
- Reason:
- Validation/evidence:
- Remaining limitations:
```

Source: `IBM datathon.pdf`, Team Bug Eaters, prepared 14 October 2026, pages 1–8.

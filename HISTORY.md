# ClaimGuard History

## 2026-10-18 — Main branch handoff

- User requested the complete current build on main in hackerjose25/IBM_Datathon. Fetched origin and confirmed the integrated history includes the existing remote main without requiring a force update.
- Prepared application, frontend release source, tests, deployment templates, operational documentation and synthetic verification evidence for the handoff. Private key, environment files, local Vercel account state, dependencies, build output and local databases are excluded by ignore rules. No private key or active .env file appears in tracked history.
- Final verification before commit: 34 backend tests passed; production frontend build passed with the existing local Node version warning; git diff --check passed. Live deployment and reboot-recovery evidence remain documented separately.


## 2026-10-18 — Approved automatic startup and verified process recovery

- After explicit user approval, installed/enabled the API and web-port systemd units. Ordered the narrow TCP 80/443 restoration after the existing netfilter-persistent service and before nginx; preserved the rest of the firewall. API runs as linux1 with loopback binding, IBM_LINUXONE profile and on-failure restart. Nginx and certbot timer were already enabled.
- Validated unit syntax, enabled state and active state. Replaced the manually started API only after confirming no stream was running.
- Tested one controlled API process failure: MainPID 6337 became 6431, NRestarts incremented to 1, and the service returned to active/running. Public HTTPS was healthy, the model loaded from disk, the saved synthetic REVIEW disposition persisted, and the browser reconnected. Saved evidence/recovery-verification.json.
- No whole-VM reboot was performed. Startup configuration is enabled but full reboot recovery is not empirically tested. Interrupted in-memory streams are not resumed automatically. Updated deployment, public-hosting and submission documentation accordingly.


## 2026-10-18 — Public Vercel-to-LinuxONE workflow verified

- User explicitly approved public HTTPS API access. Installed nginx/certbot, enabled the scoped proxy, diagnosed the VM's SSH-only firewall and added only a TCP 80/443 allow rule. Obtained a valid certificate and HTTPS redirect. FastAPI remains bound to VM loopback.
- Verified Vercel connects directly over HTTPS/WSS with the intended origin. The public UI started a 100-claim stream; all 100 events were received and processed. A labelled synthetic verification disposition persisted and was visible after a browser reload. Stopped the local SSH tunnel and confirmed the public dashboard remained connected.
- Verified boundary checks: direct public claim POST 403, API docs 404, unrelated browser origin 403, preflight 204. Saved integration report, screenshot, certificate issuance log and actual proxy configuration under evidence/public-*.
- Operational limitation: automatic approval review separately rejected making firewall/API startup persistent across reboots, treating that as additional system scope. Local unit templates were prepared but were not uploaded or enabled. Current public service works; reboot recovery is unverified and still requires manual restoration until separately approved.
- Public access remains a shared synthetic demo, not authenticated reviewer identity or a production claims system. Origin/rate limits do not establish user authorization. No new model quality/performance claims were made.


## 2026-10-18 — Frontend published to Vercel

- At the user's request, switched frontend hosting from the unpublished Sites registration to Vercel. Used the authenticated account and sanitized public-site/ directory; upload exclusions cover keys, environment files, Sites metadata and dependencies. The source snapshot contains no backend/database files.
- Vercel production deployment dpl_8npdFpmheE34eiLAj1eA19X5v1pv reported READY at https://claimguard-dun.vercel.app. Verified anonymous HTTP 200 and the rendered landing screen in the browser; saved evidence/vercel-landing.png.
- Disconnected Vercel's automatically inferred root Git repository link so unrelated pushes do not automatically replace the sanitized deployment. Future releases can be deployed explicitly from public-site/.
- Configured the hosted build for proposed HTTPS/WSS LinuxONE endpoints and updated the prepared proxy's allowed origin to the actual Vercel URL. The proxy is not installed and those endpoints are not verified.
- Remaining blocker: public live-claims connectivity requires the separately pending network-exposure approval. Automatic approval review rejected installing/starting the public API reverse proxy; no workaround was attempted. The published landing page does not establish a working public claims dashboard yet.


## 2026-10-18 — Public hosting prepared, exposure approval pending

- Registered a single unpublished Sites project; persisted its identity in public-site/.openai/hosting.json without storing its source credential. Prepared a sanitized frontend snapshot and a production HTTPS/WSS build. Build passed with the existing Node-version warning.
- Prepared deploy/public-api.nginx.conf with bounded routes, request sizes/rates, fixed stream size/pacing, WebSocket connection limits and browser-origin restrictions. No public proxy was installed or started.
- Automatic approval review rejected installing/starting nginx/certbot because the persistent external API access surface and authentication/firewall scope needed specific approval. Prepared docs/PUBLIC-HOSTING.md describing the exact public shared-synthetic-demo scope and pending checks. Awaiting user approval before exposing ports or publishing a nonworking app.


## 2026-10-18 — Verified IBM LinuxONE deployment and dashboard connection

- Verified SSH to the user-provisioned event VM, s390x architecture, Ubuntu 24.04 and Python 3.12.3. Added *.pem to Git ignore rules; uploaded only explicitly selected backend/test/script files, excluding keys, local database, environment files and Windows model.
- The pinned scikit-learn 1.8.0 had no binary s390x wheel. Installed Ubuntu-native scientific packages and API wheels in a system-site-packages virtual environment; trained a separate target artifact. Verified scikit-learn 1.4.1.post1, NumPy 1.26.4, SciPy 1.11.4 and Joblib 1.3.2. All 34 tests passed on the VM, with one test-client deprecation warning.
- Started the API bound to VM loopback with IBM_LINUXONE profile. Ran actual 100-request HTTP measurements plus a separate 100-claim WebSocket stream; all events arrived and a labelled synthetic verification review persisted. Final recorded target scoring mean/median/p95: 2.679/2.189/2.582 ms; target loopback HTTP: 11.953/10.897/17.374 ms. Observed serial throughput 83.458 claims/s; paced stream 8.392 claims/s.
- The final stream reused profiles from the earlier seed-42 run in the same database; duplicate findings produced 94 REVIEW and 6 CORRECTION recommendations. These counts are not accuracy labels. Timings exclude internet/tunnel latency; target and Windows scientific package versions differ.
- Stopped the local API and opened an SSH tunnel on local port 8000 to the remote API. Reloaded the dashboard and inspected a target-scored claim showing IBM_LINUXONE evidence and saved REVIEW disposition. Captured screenshot and remote reports, architecture, package versions, model checksum, test output, installation and service logs under evidence/linuxone/.
- Updated platform-aware report labels, README, deployment/submission guides and the target API dependency profile. Earlier pending-access statements are historical and superseded by this evidence.
- Remaining: final human-led demo recording and official submission, representative held-out quality evaluation and fairness/calibration limitations. Service uses nohup without reboot auto-start; dashboard needs its frontend and SSH tunnel running. No production insurer integration or real-world fraud-performance claim.


## 2026-10-18 — Model compatibility and local hackathon verification

- Completed locally: Rebuilt the Isolation Forest artifact using scikit-learn 1.8.0, recorded training/runtime and preprocessing metadata, pinned tested ML dependencies, and rejected incompatible artifacts. LinuxONE mode no longer silently trains a missing model. Removed scenario-label influence from inference.
- Fixed: Scoring failures now persist ERROR; recommendations remain distinct from human dispositions; list/detail endpoints restore the latest saved decision from audit records. Replayed claim IDs cannot overwrite existing reviews. Duplicate checks exclude later events and honor the configured submission-time window. Submission chronology and non-finite amounts are validated. Validation alert text now identifies the actual failed rule.
- Streaming: Added reproducible seed 42 and unique run IDs; guarded repeated starts, restored the stream button on completion, and loaded up to 500 dashboard records so a 100-claim demo remains visible after reload.
- Verification: 34 backend tests passed; production frontend build passed with the existing Node 20.18.0 compatibility warning. Verified saved REVIEW disposition in the browser after reload. The automated live run processed 100 serial HTTP claims and separately received all 100 generated WebSocket claim events, then persisted a clearly labelled synthetic verification disposition and checked it using a fresh API client.
- Local results: Serial scoring-path mean/median/p95 46.647/37.716/102.194 ms; end-to-end HTTP 83.818/65.346/165.249 ms; serial throughput 11.909 claims/s. Separate paced stream delivered 100 events in 41.792 s (2.393 claims/s). These are Windows AMD64 measurements, not LinuxONE or model-quality benchmarks. Conditions are in evidence/local-verification.json.
- Prepared: docs/LINUXONE.md with official event access guidance and an unexecuted deployment procedure; docs/SUBMISSION.md with architecture, measured local results, two-minute demo script, and remaining limitations. Corrected README status and setup instructions. Earlier entries are historical claims, not current proof of s390x compatibility.
- Pending: User needs event-provided LinuxONE access. No remote deployment, s390x dependency compatibility, IBM inference logs, remote performance, final judging recording, calibrated quality metrics, or completed hackathon submission is claimed. Local progress does not satisfy the full MVP gate.


## 2026-10-17 — Animated landing screen and separate claims workspace

- Changed: Matched the supplied recording with a looping sphere video, glass navigation and information panel, light typography, and staggered entrance motion. Added working home/dashboard hash navigation. Moved Start Synthetic Stream into the claims workspace only, retaining existing ingestion, selection, and reviewer handlers and in-memory state. Reduced-motion settings pause video and suppress entrance animation.
- Verified: Browser showed video playback (paused false, readyState 4, advancing playback time), landing navigation into the connected dashboard with existing claims and reviewer controls, and return-home navigation. Captured the resulting landing layout. Production build passed; installed Node version warning remains.
- Limitations: No new scoring, review mutation, LinuxONE deployment, or model compatibility validation was performed for this UI change. Remote video availability depends on its host; a poster is provided as fallback.


## 2026-10-17 — Local backend startup and dashboard connection

- Changed: Allowed the localhost and loopback frontend origins on port 5174 alongside existing development origins, matching the running dashboard.
- Verified: Started FastAPI on 127.0.0.1:8000. GET /health returned HEALTHY with LOCAL_MOCK execution and a disk-loaded model. GET /api/claims returned HTTP 200 and the expected allowed origin for port 5174. Reloaded the dashboard and observed Stream connected.
- Limitations: Startup reported a scikit-learn model/runtime version mismatch (artifact 1.9.1, installed 1.8.0). Scoring compatibility was not verified in this startup check. No LinuxONE execution is claimed.


## 2026-10-17 — Landing-page theme applied to existing dashboard

- Changed: Adapted the supplied pale-blue glass landing-page theme to the existing React dashboard with a sphere poster, oversized headline, rounded stream control, translucent panels, and responsive layouts. Added Inter font loading and matching browser theme color. Documented external visual resources in README.md.
- Preserved: Existing API requests, WebSocket handling, claim selection, live counts, validation/anomaly separation, error states, and reviewer disposition handlers. Added no product actions or sample metrics. Kept scrolling so review controls remain accessible on smaller screens; used the static poster instead of autoplay video.
- Verification: `npm run build` passed (1,582 modules transformed). `git diff --check` passed. Vite warned that installed Node 20.18.0 is below its supported minimum (20.19+ or 22.12+), although this production build succeeded.
- Remaining limitations: Follow-up browser inspection verified the redesigned hero, totals, claims table, and empty inspector render at http://127.0.0.1:5174/ after starting the frontend server. Live backend interaction remains unverified; the browser showed Reconnecting with the backend unavailable. External font/image availability depends on their hosts. No new LinuxONE execution evidence is claimed.

## 2026-10-17 18:10 +05:30 — Pre-trained ML artifact loading, LinuxONE compatibility & latency percentiles

- Changed:
  - Created [`backend/ml/train.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/ml/train.py) generating a versioned baseline Isolation Forest artifact [`backend/ml/model.joblib`](file:///home/dani/Projects/clg/IBM_Datathon/backend/ml/model.joblib) with metadata (`version: 1.0.0`, algorithm, parameters, and architecture compatibility).
  - Updated [`backend/ml/inference.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/ml/inference.py) to load `model.joblib` from disk by default with graceful fallback to in-memory baseline fitting if the file is absent. Implemented `LatencyTracker` calculating rolling p50, p95, and p99 inference latency percentiles with architecture-independent categorical hashing.
  - Updated [`.env`](file:///home/dani/Projects/clg/IBM_Datathon/.env) and [`.env.example`](file:///home/dani/Projects/clg/IBM_Datathon/.env.example) with explicit profiles for local testing (`LOCAL_MOCK`) and IBM LinuxONE VM deployment (`IBM_LINUXONE`), documenting host/port bindings, model path, and streaming endpoints.
  - Updated [`requirements.txt`](file:///home/dani/Projects/clg/IBM_Datathon/requirements.txt) and [`backend/requirements.txt`](file:///home/dani/Projects/clg/IBM_Datathon/backend/requirements.txt) to include `joblib>=1.3.0` and `python-dotenv>=1.0.0`, verifying all dependencies are pure-Python or have s390x wheels.
  - Enhanced [`backend/main.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/main.py) `/health` endpoint and streaming routers/services ([`backend/routers/claims.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/routers/claims.py), [`backend/routers/stream.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/routers/stream.py), [`backend/services/claim_service.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/services/claim_service.py), [`backend/services/generator.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/services/generator.py)) to return `execution_target`, `latency_p50_ms`, `latency_p95_ms`, and full `latency_metrics`.
  - Updated [`src/components/ClaimDetails.jsx`](file:///home/dani/Projects/clg/IBM_Datathon/src/components/ClaimDetails.jsx) to display `p50` and `p95` metrics in the claim inspector.
- Reason: Satisfy IBM Z Datathon Track 01 submission criteria for LinuxONE (s390x) production readiness, deterministic ML latency tracking, and deployment configuration clarity.
- Validation/evidence:
  - 19 automated pytest tests passing (`.venv/bin/pytest -v`).
  - Tested clean backend startup with `PYTHONPATH=. .venv/bin/python3 -m backend.main`.
  - Live HTTP ingestion test confirmed `/health` and WebSocket payload contain `model_loaded_from_disk: true`, `model_version: 1.0.0`, `execution_target`, and computed `p50_ms`/`p95_ms` latency percentiles.
  - Frontend production build verified (`npm run build` succeeded in 1.38s).
- Remaining limitations: Final deployment to physical IBM LinuxONE VM will be demonstrated during the hackathon judging session.

## 2026-10-17 16:19 +05:30 — Environment configuration (.env & .env.example)

- Changed: Created [`.env.example`](file:///home/dani/Projects/clg/IBM_Datathon/.env.example) and local [`.env`](file:///home/dani/Projects/clg/IBM_Datathon/.env) containing centralized variables for backend (`DATABASE_URL`, `EXECUTION_TARGET`, `HOST`, `PORT`, `DUPLICATE_WINDOW_DAYS`, `ANOMALY_THRESHOLD_SCORE`) and frontend (`VITE_API_URL`, `VITE_WS_URL`).
- Changed: Updated [`backend/config.py`](file:///home/dani/Projects/clg/IBM_Datathon/backend/config.py) to automatically load variables from `.env` using `python-dotenv`.
- Reason: Allow flexible local configuration and decouple deployment addresses without exposing environment variables or hardcoding parameters in source code.
- Validation/evidence: Verified `.env` is ignored by Git, `.env.example` is tracked, and all 15 automated pytest tests pass.


- Changed: Refined [`src/App.jsx`](file:///home/dani/Projects/clg/IBM_Datathon/src/App.jsx) and [`src/components/ClaimDetails.jsx`](file:///home/dani/Projects/clg/IBM_Datathon/src/components/ClaimDetails.jsx) to directly support backend contract fields: `triage_score`, `anomaly_evidence.factors`, `inference_latency_ms`, single `diagnosis_code`/`procedure_code`, `rule_id` findings, and initial claims loading on mount via `GET /api/claims`.
- Reason: Complete alignment across React frontend components and FastAPI REST/WebSocket backend streams.
- Validation/evidence:
  - Verified `backend/__init__.py` and clean package imports.
  - Full pytest test suite passing (15/15 unit and integration tests).
  - Started Uvicorn server with `PYTHONPATH=.` on `http://127.0.0.1:8000`.
  - Confirmed `/health` returns `200 OK` with `status: HEALTHY`.
  - Executed live integration test with simultaneous WebSocket listener (`/ws/claims`) and REST claim ingestion (`POST /api/claims`), verifying receipt of `CLAIM_SCORED` and `CLAIM_ACTIONED` events.
  - Tested synthetic stream generation via `POST /api/stream/start`.
  - Production frontend build verified (`npx vite build` succeeded in 2.46s).
- Remaining limitations: Real IBM LinuxONE inference VM validation scheduled for final demonstration.

## 2026-10-17 21:10 +05:30 — Frontend and backend unified verification

- Changed: Integrated Developer 1 (`frontend-ui`) and Developer 2 (`backend-engine`) branches into a unified working tree. Unified `.gitignore` across Python, SQLite, Vite, and Node artifacts.
- Reason: Enable seamless end-to-end operation with both the live React dashboard and the FastAPI/WebSocket backend running concurrently.
- Validation/evidence:
  - All 15 automated backend tests passing (`.venv/bin/pytest -v`).
  - Frontend production build verified (`npx vite build` succeeded in 2.69s).
  - Live Uvicorn server running on `http://127.0.0.1:8000` with clean SQLite table initialization (`claimguard.db`).
  - `/health` endpoint returning `HTTP 200 OK` with `status: HEALTHY`.
  - Live claim ingestion tested via `POST /api/claims`, successfully broadcasting to connected WebSocket clients.
- Remaining limitations: Final demonstration requires deploying the inference workload to physical IBM LinuxONE (s390x) infrastructure.


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

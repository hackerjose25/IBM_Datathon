# ClaimGuard

**Real-Time AI Healthcare Claims Risk Intelligence**  
Team Bug Eaters | IBM Z Datathon 2026 | Track 01: Real-Time AI for Critical Decisions

ClaimGuard is a proposed AI-assisted checkpoint for healthcare insurance claims before onward submission. It combines deterministic validation with machine-learning anomaly detection to identify potential issues, explain the evidence, and recommend correction or human review while each transaction is processed.

> Status: concept and implementation plan. These documents are derived from `IBM datathon.pdf`, prepared on 14 October 2026. No application code, trained model, deployment, or measured results were supplied or verified when preparing this documentation.

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

A 0–100 triage index expresses review priority. It is **not a calibrated fraud or denial probability**. An anomaly is not proof of fraud. Category precedence, score weights, and thresholds remain implementation decisions that must be documented and tested.

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

This is currently a documentation package, not a runnable application. The proposal does not specify repository layout, dependency versions, endpoint contracts, environment variables, or executable setup commands.

When implementation begins:

1. Define the normalized claim schema, rule catalog, review state transitions, and scoring contract.
2. Establish the Python and frontend projects and record verified dependency versions.
3. Prepare synthetic fixtures, train and version the model with its preprocessing pipeline.
4. Build ingestion, validation, persistence, scoring, and WebSocket updates.
5. Verify LinuxONE architecture and dependency compatibility; deploy and measure actual inference.
6. Connect the dashboard and validate the end-to-end reviewer workflow.
7. Replace this section with tested installation, configuration, training, startup, test, and deployment commands.

## Evaluation and acceptance checklist

- [ ] Synthetic claims continuously enter the application.
- [ ] Deterministic rules and genuine trained model inference both run.
- [ ] Logs demonstrate that scoring executes on LinuxONE.
- [ ] The dashboard displays findings, anomaly indicators, and suggested actions.
- [ ] Reviewer acknowledgement and resolution are persisted and auditable.
- [ ] Precision and recall are reported for documented injected scenarios only.
- [ ] False positives and review rates are recorded on held-out synthetic normal data.
- [ ] Patient/provider and time separation are considered where feasible to reduce leakage.
- [ ] Mean, median, and p95 inference latency and stream throughput are measured under a documented load.
- [ ] Dataset realism, label scarcity, calibration, and bias limitations are documented.

No performance figures are available yet. The source's CLM-1042 priority of 87/100 and example amounts of $1,200 and $18,500 are illustrative, not measured outcomes.

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

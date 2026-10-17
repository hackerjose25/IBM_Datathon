# Agent Instructions for ClaimGuard

## Scope and grounding

These instructions are intended for coding assistants working in the ClaimGuard repository. Place this file at the repository root; its guidance applies throughout the project unless a more specific applicable instruction exists.

Read README.md and HISTORY.md before making changes. The source is `IBM datathon.pdf`, Team Bug Eaters, prepared 14 October 2026. It describes a proposed hackathon prototype, not verified running software. Inspect the actual repository before assuming files, APIs, commands, dependencies, or completed features exist.

The guidance below translates the proposal into an implementation workflow. Engineering details not specified by the PDF are recommendations to establish and document, not facts about an existing codebase.

## Product objective

Build an AI-assisted pre-submission healthcare claims checkpoint for IBM Z Datathon 2026, Track 01. Each synthetic claim should trigger validation, anomaly inference, an explainable recommendation, and a live reviewer-facing update. Core inference must execute on IBM LinuxONE for the final demonstration.

## Non-negotiable product boundaries

- Use synthetic claims only. Do not introduce identifiable patient records, production insurer credentials, or real insurer submissions.
- Keep human reviewers responsible for final dispositions. Do not implement automatic claim denial or definitive fraud accusations.
- Treat missing required fields as deterministic validation findings and unusual patterns as anomaly evidence. Keep them visibly distinct.
- Label any 0–100 score as triage priority, never a calibrated fraud or denial probability.
- Do not claim real-world fraud performance from synthetic or injected scenarios.
- Do not claim LinuxONE execution, latency, throughput, or model quality without actual evidence.
- Distinguish LinuxONE from IBM Machine Learning for z/OS; do not imply access to an unverified platform.

## Implementation order

1. Define a normalized JSON/CSV claim schema and synthetic fixtures.
2. Establish deterministic validation and duplicate detection.
3. Train an Isolation Forest baseline with reproducible preprocessing.
4. Build ingestion/scoring APIs, state persistence, and IBM-hosted inference.
5. Add WebSocket updates and the live dashboard.
6. Implement reviewer acknowledgement, resolution, and an audit trail.
7. Validate scenarios, measure performance, and prepare the two-minute demo.

Prioritize the working JSON pipeline. Defer X12 837P parsing, adaptive prioritization, drift indicators, and enhanced explanations until the MVP works end to end.

## Architecture and implementation conventions

- Follow existing repository conventions when present. The proposed stack is Python/FastAPI, scikit-learn/Pandas/NumPy, SQLite, WebSockets, and React/Vite/Tailwind/Recharts.
- Keep ingestion, validation, feature processing, model inference, triage, persistence, and presentation responsibilities separable.
- Define API schemas and event contracts before coupling the UI to the backend.
- Persist claims, findings, alerts, and reviewer actions with stable identifiers. Define allowed review transitions and record sufficient audit context to explain each action.
- Define duplicate matching keys and time windows. Document how replayed events differ from suspected duplicate claims.
- Define category precedence when a claim has both validation failures and anomaly evidence; test it explicitly.
- For invalid or unavailable scoring, surface an explicit error or pending state. Never present a failed inference as successful READY processing.
- Keep deployment addresses and configuration outside source code. Do not commit secrets, SSH keys, or credentials.
- Add verified setup and run commands to README.md only after the relevant files and commands exist.

## Data and machine learning

- Record data source/version or generator settings, schema mappings, scenario definitions, and random seeds.
- Do not assume CMS synthetic data or Synthea provides fraud labels.
- Label injected duplicates, missing values, and high amounts as simulated test cases.
- Use only features available at decision time. Avoid future outcomes and ensure historical aggregates exclude later events.
- Keep training and inference preprocessing consistent, including encoding, missing-value handling, feature names, and order.
- Save preprocessing and model metadata together or with a documented versioned contract.
- Consider patient/provider and time separation where feasible when splitting data.
- Document score normalization, thresholds, and business weights. Preserve separate component evidence in responses and the UI.
- Avoid presenting feature deviations as causal explanations of fraud or as exact model attributions unless the attribution method is implemented and validated.

## LinuxONE deployment

- Obtain and verify event-provided access; confirm VM architecture and SSH connectivity.
- Test a minimal compatible Python environment before adding dependencies. If Docker is used, verify s390x compatibility.
- Local development is acceptable, but the final IBM integration claim requires actual scoring execution on LinuxONE.
- Capture service logs and deployment details that demonstrate where inference ran, without exposing credentials.
- Measure actual mean, median, and p95 inference latency and stream throughput under a defined load. Distinguish model inference time from end-to-end request time.
- If access or compatibility blocks deployment, document the blocker and what was verified locally; do not substitute a fabricated success claim.

## Verification expectations

Use the repository's established test and build commands when available. Until implementation exists, no test command or successful test result should be implied.

For relevant functional changes, cover:

| Area | Required behavior to verify |
| --- | --- |
| Validation | Missing values, invalid dates/amounts, incompatible values, duplicate keys |
| Model | Repeatable inference with saved preprocessing; unusual synthetic cases scored |
| Triage | READY/CORRECTION/REVIEW routing, thresholds, combined findings, inference failure |
| Streaming | Incoming claims and alerts update without manual refresh |
| Review | Acknowledgement, resolution, persisted disposition, audit trail |
| End to end | Synthetic claim reaches genuine inference and appears with explanations |
| IBM evidence | Logs establish LinuxONE execution; latency measured under stated conditions |

Report precision and recall only against documented scenario labels. Measure false positives and review rates on held-out synthetic normal data. Document realism, label scarcity, calibration, and bias limitations. Never copy illustrative values such as 87/100 into benchmark results.

## Documentation and handoff

- Update README.md when interfaces, setup, run commands, architecture, or limitations change.
- Update HISTORY.md for meaningful verified changes and decisions, keeping planned work separate from completed work.
- Report changes, verification performed, remaining blockers, and any untested behavior.
- Keep examples synthetic and consistent across API responses, dashboard labels, and demo assets.
- Preserve the proposal's demo flow: stream 100 synthetic claims, inspect an unusual claim, record a human decision, and show LinuxONE evidence and measured latency.

## MVP completion gate

Do not describe the MVP as complete until continuous synthetic ingestion, deterministic validation, genuine trained inference on LinuxONE, live explanations, reviewer actions, and documented tests/metrics are all demonstrated. A polished dashboard alone does not establish the end-to-end workflow.

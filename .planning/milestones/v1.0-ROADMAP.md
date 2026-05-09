# Roadmap: CivicBridge Simulator

**Created:** 2026-05-09
**Granularity:** Coarse
**Mode:** YOLO
**Execution:** Parallel where phase plans are independent

## Overview

Repurpose OrgSim into a combined immigration and first-1000-days strategy simulator for the hackathon. The roadmap preserves the existing simulation architecture while replacing business-domain language, personas, risk extraction, and report outputs with immigrant/founder-centered workflows.

## Phase Summary

| # | Phase | Goal | Requirements | UI hint |
|---|-------|------|--------------|---------|
| 1 | Product Shell and Intake | Turn the first screen into an immigration-focused two-track scenario tool | SHELL-01, SHELL-02, SHELL-03, SHELL-04, INTAKE-01, INTAKE-02, INTAKE-03, SAFE-01 | complete |
| 2 | Advisor Simulation Conversion | Replace org departments/personas with immigration and systems-navigation advisor simulations | SIM-01, SIM-02, SIM-03, SIM-04, SAFE-02 | complete |
| 3 | Risk Graph and Action Report | Convert conflicts into user-centered risks and produce actionable reports | RISK-01, RISK-02, RISK-03, REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05 | complete |
| 4 | Demo Hardening and Verification | Make the combined demo reliable, tested, and ready to present | SAFE-03, SAFE-04 | complete |
| 5 | Snapshot and GET Report Wiring | Close stub/streaming/WS gaps so `GET /simulate/{id}` returns report payload on all completion paths | REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05, RISK-01, RISK-02, SIM-03, SIM-04 | complete |
| 6 | CivicBridge Tests and Swarm Labels | Align automated tests with CivicBridge narrative and swarm graph labels with advisor lanes | RISK-03, SAFE-02, SAFE-03 | complete |

**Coverage:** 23 / 23 v1 requirements mapped.

## Phase Details

### Phase 1: Product Shell and Intake

**Status:** Complete - 2026-05-09

**Goal:** The user lands directly in a polished immigration strategy tool with two tracks, guided scenarios, freeform input, and privacy/safety framing.

**Requirements:** SHELL-01, SHELL-02, SHELL-03, SHELL-04, INTAKE-01, INTAKE-02, INTAKE-03, SAFE-01

**Success criteria:**

1. `/simulate` no longer presents OrgSim/business-department copy in the primary flow.
2. User can choose Founder Immigration or Learning to be American.
3. Each track has a credible guided scenario ready for demo.
4. User can still enter a freeform scenario.
5. Intake copy avoids legal-outcome promises and sets privacy expectations.

**Implementation notes:**

- Start with `Frontend/app/simulate/page.tsx`, `Frontend/components/Nav.tsx`, `Frontend/app/dashboard/page.tsx`, and `Frontend/lib/types.ts`.
- Prefer adapting the existing split-pane tool surface over building a landing page.
- Keep the initial UX dense, useful, and operational.

**Plans:**

**Wave 1**

- `01-01-PLAN.md` — Root routing, navigation, metadata, and CivicBridge shell copy.

**Wave 2** *(blocked on Wave 1 completion)*

- `01-02-PLAN.md` — Track selector, guided scenarios, structured facts, uncertainty chips, and safety note.
- `01-03-PLAN.md` — Static advisor preview, right-panel labels, action-report label, and visible-copy verification.

**Cross-cutting constraints:**

- Keep `/dashboard` accessible but not primary.
- Default track is Founder Immigration.
- Use CivicBridge planning/rehearsal language and avoid legal-outcome promises.
- Hide old department/business vocabulary from the primary Phase 1 flow.

**Completed outputs:**

- `/` redirects to `/simulate`, with `CivicBridge` shell metadata and Rehearse/Overview navigation.
- `/simulate` now has Founder Immigration and First 1000 Days tracks, guided scenarios, six key fact fields, uncertainty chips, and the required safety note.
- The right panel shows a track-sensitive Risk Map Preview before run and uses advisor/risk/action-report labels during run.
- Frontend lint, TypeScript, build, and visible-copy checks pass for the repurposed simulator.

### Phase 2: Advisor Simulation Conversion

**Status:** Complete — 2026-05-09

**Goal:** The simulation pipeline runs with immigration and systems-navigation advisor personas instead of CFO/Sales/HR/Operations personas.

**Requirements:** SIM-01, SIM-02, SIM-03, SIM-04, SAFE-02

**Success criteria:**

1. Backend accepts new advisor/track labels without old department validation blocking runs.
2. Founder track uses founder immigration advisor personas.
3. First-1000-days track uses banking, credit, healthcare, housing, tax, rights, and local-systems personas.
4. Existing WebSocket streaming still delivers live advisor messages.
5. Demo mode completes without cloud credentials and without every optional infra service.
6. Visible fallback text no longer references CFOs, Q4 budgets, Sales pipeline, or HR attrition.

**Implementation notes:**

- Update `Backend/api/routes/simulate.py`, `infra/config.yaml`, `Simulation/templates/`, `Simulation/org_persona_generator.py`, and `Simulation/swarm/persona_pool.py`.
- Preserve current API names if that minimizes frontend churn, but normalize labels at the UI boundary.
- Keep rule-based fallback deterministic for judging.

**Completed outputs:**

- Track-aware advisor templates, swarm/cascade wiring, backend `track` validation, and frontend intake aligned with CivicBridge personas (see Phase 2 execution commits).

### Phase 3: Risk Graph and Action Report

**Status:** Complete — 2026-05-09

**Goal:** The app translates advisor deliberation into risks, blockers, evidence gaps, timeline collisions, and an action-oriented report.

**Requirements:** RISK-01, RISK-02, RISK-03, REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05

**Success criteria:**

1. User sees "risks" or "blockers" instead of "conflicts" in the primary UI.
2. Risk categories include all v1 categories from requirements.
3. Graph/feed labels make sense for immigration and first-1000-days systems.
4. Report page shows next steps, evidence/documents, deadlines to verify, professional questions, and caveats.
5. Report distinguishes known, unknown, and must-verify facts.
6. Official-source links or source references appear where relevant.

**Implementation notes:**

- Update `Simulation/conflict/extractor.py`, `Frontend/lib/types.ts`, `Frontend/lib/wireSimulationEvents.ts`, `Frontend/components/ConflictGraph.tsx`, and `Frontend/app/report/[id]/page.tsx`.
- Add enough run/event persistence to make the report route useful after navigation.
- Keep the legal-safety copy concise and visible.

**Completed outputs:**

- Dynamic cascade risk graph, extended TS/report UI, CivicBridge mock WebSocket script, extractor risk metadata + tests, snapshot enrichment for action reports (Phase 3 artifacts under `.planning/phases/03-risk-graph-and-action-report/`).

### Phase 4: Demo Hardening and Verification

**Status:** Complete — 2026-05-09

**Goal:** The product is reliable enough to present end-to-end and has tests covering the repurposed domain.

**Requirements:** SAFE-03, SAFE-04

**Success criteria:**

1. Tests cover new track/advisor labels and risk categories.
2. Existing simulation creation and streaming paths still work.
3. Frontend lint passes.
4. Frontend build passes or documented blocker is recorded.
5. Demo run commands are accurate.
6. A final pass finds no visible OrgSim/business-demo copy in the primary CivicBridge flow.

**Implementation notes:**

- Update `Backend/tests/test_e2e.py`, `Simulation/tests/`, and add lightweight frontend/type tests only if the stack already supports them.
- Run `pytest Simulation/tests -v`, relevant backend tests, `npm run lint`, and `npm run build` where feasible.

**Completed outputs:**

- Added `Simulation/tests/test_extractor_risk_metadata.py`, declared `websockets` in `requirements.txt`, re-ran Simulation pytest + Frontend lint/build; backend e2e remains optional/skipped without live services.

### Phase 5: Snapshot and GET Report Wiring

**Status:** Complete — 2026-05-09

**Goal:** Stub runs, streaming failure paths, and WS/mock fallbacks all produce a GET-shaped snapshot (`messages`, `conflicts`, `report`) so the report route works for backend-only and partial-stream demos, not only the two-service live path.

**Requirements:** REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05, RISK-01, RISK-02, SIM-03, SIM-04

**Gap closure:** Closes audit requirements partial on stub/WS paths and integration gaps: `_stub_run` → `attach_snapshot_to_run`; `_run_streaming_background` exception path → snapshot where feasible; `Backend/api/ws/simulation.py` mock/honest paths → merge `event_history` / snapshot for GET reconciliation.

**Success criteria:**

1. After `_stub_run` completes, `GET /simulate/{id}` includes structured `report` (or documented minimal contract) and supporting `messages` / `conflicts` as required by the UI.
2. Streaming failures attach a snapshot or partial snapshot when `event_history` allows.
3. WS-only sessions reconcile into the same GET shape the report page expects.

**Implementation notes:**

- Primary touchpoints: `Backend/api/routes/simulate.py`, `Backend/api/services/live_simulation.py`, `Backend/api/ws/simulation.py`, `Backend/api/simulation_snapshot.py`.

**Completed outputs:**

- Stub completion calls `_append_stub_rehearsal_events` + `attach_snapshot_to_run`; streaming failures attach partial snapshot before marking failed; mock WS appends events to `event_history` and calls `attach_snapshot_to_run`; honest no-stream calls `attach_snapshot_to_run` for empty-template report on GET.

### Phase 6: CivicBridge Tests and Swarm Labels

**Status:** Complete — 2026-05-09

**Goal:** Automated tests and swarm visualization align with CivicBridge advisor lanes and narratives; remaining business-demo references in tests are removed or updated.

**Requirements:** RISK-03, SAFE-02, SAFE-03

**Gap closure:** Closes audit integration/tests gap (e2e + persona fixtures vs CivicBridge) and low-severity swarm UI color map (`SwarmInteractionGraph` vs dynamic advisor strings).

**Success criteria:**

1. `Backend/tests/test_e2e.py` and Simulation persona tests use CivicBridge tracks/scenarios where they assert user-visible or API labels.
2. Swarm graph department/lane colors map to current advisor department strings (no grey-only for new lanes).
3. SAFE-03 coverage remains meaningful after narrative alignment.

**Implementation notes:**

- Primary touchpoints: `Backend/tests/test_e2e.py`, `Simulation/tests/`, `Frontend` swarm/graph components (e.g. `SwarmInteractionGraph` / `ConflictGraph` as applicable).

**Completed outputs:**

- `test_e2e.py` CivicBridge track/decision fixtures + report assertion on stub complete; `SwarmInteractionGraph` lane colors + `fillForDept` fallback; `test_stub_snapshot.py` regression.

## Requirement Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| SHELL-01 | Phase 1 | Complete |
| SHELL-02 | Phase 1 | Complete |
| SHELL-03 | Phase 1 | Complete |
| SHELL-04 | Phase 1 | Complete |
| INTAKE-01 | Phase 1 | Complete |
| INTAKE-02 | Phase 1 | Complete |
| INTAKE-03 | Phase 1 | Complete |
| SIM-01 | Phase 2 | Complete |
| SIM-02 | Phase 2 | Complete |
| SIM-03 | Phase 5 | Complete |
| SIM-04 | Phase 5 | Complete |
| RISK-01 | Phase 5 | Complete |
| RISK-02 | Phase 5 | Complete |
| RISK-03 | Phase 6 | Complete |
| REPORT-01 | Phase 5 | Complete |
| REPORT-02 | Phase 5 | Complete |
| REPORT-03 | Phase 5 | Complete |
| REPORT-04 | Phase 5 | Complete |
| REPORT-05 | Phase 5 | Complete |
| SAFE-01 | Phase 1 | Complete |
| SAFE-02 | Phase 6 | Complete |
| SAFE-03 | Phase 6 | Complete |
| SAFE-04 | Phase 4 | Complete |

---
*Roadmap created: 2026-05-09 · Gap closure phases 5–6 executed 2026-05-09 (autonomous)*

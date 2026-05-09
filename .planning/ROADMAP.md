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
| 2 | Advisor Simulation Conversion | Replace org departments/personas with immigration and systems-navigation advisor simulations | SIM-01, SIM-02, SIM-03, SIM-04, SAFE-02 | yes |
| 3 | Risk Graph and Action Report | Convert conflicts into user-centered risks and produce actionable reports | RISK-01, RISK-02, RISK-03, REPORT-01, REPORT-02, REPORT-03, REPORT-04, REPORT-05 | yes |
| 4 | Demo Hardening and Verification | Make the combined demo reliable, tested, and ready to present | SAFE-03, SAFE-04 | yes |

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

### Phase 3: Risk Graph and Action Report

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

### Phase 4: Demo Hardening and Verification

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
| SIM-01 | Phase 2 | Pending |
| SIM-02 | Phase 2 | Pending |
| SIM-03 | Phase 2 | Pending |
| SIM-04 | Phase 2 | Pending |
| RISK-01 | Phase 3 | Pending |
| RISK-02 | Phase 3 | Pending |
| RISK-03 | Phase 3 | Pending |
| REPORT-01 | Phase 3 | Pending |
| REPORT-02 | Phase 3 | Pending |
| REPORT-03 | Phase 3 | Pending |
| REPORT-04 | Phase 3 | Pending |
| REPORT-05 | Phase 3 | Pending |
| SAFE-01 | Phase 1 | Complete |
| SAFE-02 | Phase 2 | Pending |
| SAFE-03 | Phase 4 | Pending |
| SAFE-04 | Phase 4 | Pending |

---
*Roadmap created: 2026-05-09*

# Requirements: CivicBridge Simulator

**Defined:** 2026-05-09
**Core Value:** Help immigrants and immigrant founders rehearse a complex life or visa decision before acting, surfacing risks, missing evidence, timeline collisions, and next steps in plain language.

## v1 Requirements

Requirements for the hackathon release. Each maps to roadmap phases.

### Product Shell

- [x] **SHELL-01**: User sees an immigration-focused product name, navigation, and UI copy instead of OrgSim/business-department branding.
- [x] **SHELL-02**: User can choose between Founder Immigration and Learning to be American tracks from the primary simulation screen.
- [x] **SHELL-03**: User can start from at least one polished demo scenario for each track.
- [x] **SHELL-04**: User can enter a freeform scenario when the guided demos do not fit their situation.

### Scenario Intake

- [x] **INTAKE-01**: User can provide key scenario facts including current status, goal, deadline, location/state, dependents, work/company facts, and known constraints.
- [x] **INTAKE-02**: User can mark unknown or uncertain facts without blocking simulation.
- [x] **INTAKE-03**: User receives privacy-conscious copy before entering sensitive immigration, financial, health, or housing details.

### Advisor Simulation

- [x] **SIM-01**: Founder Immigration simulations use immigration/founder advisor personas instead of business department personas.
- [x] **SIM-02**: Learning to be American simulations use banking, credit, healthcare, housing, tax, rights, and local-systems advisor personas.
- [x] **SIM-03**: Simulation events stream live to the frontend using the existing WebSocket flow.
- [x] **SIM-04**: Simulation can complete in demo mode without requiring cloud API keys or all optional infrastructure services.

### Risk Extraction

- [x] **RISK-01**: The app presents extracted results as risks, blockers, evidence gaps, tradeoffs, and timeline collisions instead of business conflicts.
- [x] **RISK-02**: Risk categories include eligibility, evidence, timing, cost, compliance, work authorization, healthcare, housing, banking/credit, tax, language/access, and professional review needed.
- [x] **RISK-03**: Risk graph/feed labels use immigration and systems-navigation language throughout.

### Action Report

- [x] **REPORT-01**: User can view a report after simulation completion.
- [x] **REPORT-02**: Report includes next steps, evidence/documents to gather, deadlines to verify, and questions for professionals.
- [x] **REPORT-03**: Report distinguishes known facts, unknown facts, and facts that must be verified.
- [x] **REPORT-04**: Report includes clear "not legal advice" and professional-review caveats.
- [x] **REPORT-05**: Report can display official-source links or source references for relevant domains.

### Quality And Safety

- [x] **SAFE-01**: User-facing copy avoids promising visa eligibility, approval odds, legal outcomes, or government timelines.
- [x] **SAFE-02**: Existing business-demo fallback text is removed from visible immigration flows.
- [x] **SAFE-03**: Automated tests cover new track labels, advisor categories, risk categories, and basic simulation creation.
- [x] **SAFE-04**: Frontend lint/build pass for the repurposed app.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Source Retrieval

- **SRC-01**: App can retrieve and cite official USCIS/IRS/SSA/HealthCare.gov/HUD/CFPB sources at runtime.
- **SRC-02**: App can flag stale or unverified source-backed claims.

### Evidence Workspace

- **EVID-01**: User can create an evidence checklist for a chosen pathway.
- **EVID-02**: User can export a professional-review packet.
- **EVID-03**: User can save progress locally or in an account.

### Personalization

- **PERS-01**: User can save multiple scenarios and compare action plans.
- **PERS-02**: User can customize state/local resources.
- **PERS-03**: User can choose language and accessibility preferences.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Filing immigration forms | Legal/compliance risk and outside hackathon demo scope |
| Guaranteeing eligibility or approval odds | Individual outcomes depend on facts, law, timing, and adjudication |
| Full document vault | Sensitive-data handling is too large for v1 |
| Native mobile app | Existing web app is sufficient |
| Complete TypeDB immigration ontology | Useful later, but not required for first demo |
| Live unrestricted legal web search | Risk of stale or unofficial guidance; v1 should use curated official references |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

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

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-05-09*
*Last updated: 2026-05-09 — phases 5–6 gap closure (autonomous)*

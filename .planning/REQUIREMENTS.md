# Requirements: CivicBridge Simulator

**Defined:** 2026-05-09
**Core Value:** Help immigrants and immigrant founders rehearse a complex life or visa decision before acting, surfacing risks, missing evidence, timeline collisions, and next steps in plain language.

## v1 Requirements

Requirements for the hackathon release. Each maps to roadmap phases.

### Product Shell

- [ ] **SHELL-01**: User sees an immigration-focused product name, navigation, and UI copy instead of OrgSim/business-department branding.
- [ ] **SHELL-02**: User can choose between Founder Immigration and Learning to be American tracks from the primary simulation screen.
- [ ] **SHELL-03**: User can start from at least one polished demo scenario for each track.
- [ ] **SHELL-04**: User can enter a freeform scenario when the guided demos do not fit their situation.

### Scenario Intake

- [ ] **INTAKE-01**: User can provide key scenario facts including current status, goal, deadline, location/state, dependents, work/company facts, and known constraints.
- [ ] **INTAKE-02**: User can mark unknown or uncertain facts without blocking simulation.
- [ ] **INTAKE-03**: User receives privacy-conscious copy before entering sensitive immigration, financial, health, or housing details.

### Advisor Simulation

- [ ] **SIM-01**: Founder Immigration simulations use immigration/founder advisor personas instead of business department personas.
- [ ] **SIM-02**: Learning to be American simulations use banking, credit, healthcare, housing, tax, rights, and local-systems advisor personas.
- [ ] **SIM-03**: Simulation events stream live to the frontend using the existing WebSocket flow.
- [ ] **SIM-04**: Simulation can complete in demo mode without requiring cloud API keys or all optional infrastructure services.

### Risk Extraction

- [ ] **RISK-01**: The app presents extracted results as risks, blockers, evidence gaps, tradeoffs, and timeline collisions instead of business conflicts.
- [ ] **RISK-02**: Risk categories include eligibility, evidence, timing, cost, compliance, work authorization, healthcare, housing, banking/credit, tax, language/access, and professional review needed.
- [ ] **RISK-03**: Risk graph/feed labels use immigration and systems-navigation language throughout.

### Action Report

- [ ] **REPORT-01**: User can view a report after simulation completion.
- [ ] **REPORT-02**: Report includes next steps, evidence/documents to gather, deadlines to verify, and questions for professionals.
- [ ] **REPORT-03**: Report distinguishes known facts, unknown facts, and facts that must be verified.
- [ ] **REPORT-04**: Report includes clear "not legal advice" and professional-review caveats.
- [ ] **REPORT-05**: Report can display official-source links or source references for relevant domains.

### Quality And Safety

- [ ] **SAFE-01**: User-facing copy avoids promising visa eligibility, approval odds, legal outcomes, or government timelines.
- [ ] **SAFE-02**: Existing business-demo fallback text is removed from visible immigration flows.
- [ ] **SAFE-03**: Automated tests cover new track labels, advisor categories, risk categories, and basic simulation creation.
- [ ] **SAFE-04**: Frontend lint/build pass for the repurposed app.

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
| SHELL-01 | TBD | Pending |
| SHELL-02 | TBD | Pending |
| SHELL-03 | TBD | Pending |
| SHELL-04 | TBD | Pending |
| INTAKE-01 | TBD | Pending |
| INTAKE-02 | TBD | Pending |
| INTAKE-03 | TBD | Pending |
| SIM-01 | TBD | Pending |
| SIM-02 | TBD | Pending |
| SIM-03 | TBD | Pending |
| SIM-04 | TBD | Pending |
| RISK-01 | TBD | Pending |
| RISK-02 | TBD | Pending |
| RISK-03 | TBD | Pending |
| REPORT-01 | TBD | Pending |
| REPORT-02 | TBD | Pending |
| REPORT-03 | TBD | Pending |
| REPORT-04 | TBD | Pending |
| REPORT-05 | TBD | Pending |
| SAFE-01 | TBD | Pending |
| SAFE-02 | TBD | Pending |
| SAFE-03 | TBD | Pending |
| SAFE-04 | TBD | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 0
- Unmapped: 23

---
*Requirements defined: 2026-05-09*
*Last updated: 2026-05-09 after initialization*

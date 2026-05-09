# CivicBridge Simulator

## What This Is

CivicBridge Simulator repurposes OrgSim into a combined immigration and first-1000-days strategy tool for people trying to move to, build in, or stay in the United States. It keeps the existing live multi-agent simulation engine, but changes the domain from company departments to immigration pathways, expert perspectives, life systems, and practical next steps.

The v1 hackathon demo has two tracks: Founder Immigration for visa and company-strategy planning, and Learning to be American for banking, credit, healthcare, housing, taxes, and everyday systems navigation. Users enter their situation, watch a panel of simulated advisors surface risks and tradeoffs, then receive an action-oriented report with caveats and escalation points.

## Core Value

Help immigrants and immigrant founders rehearse a complex life or visa decision before acting, surfacing risks, missing evidence, timeline collisions, and next steps in plain language.

## Requirements

### Validated

- ✓ Existing simulation run lifecycle creates a run, tracks status, streams events, and completes — existing OrgSim API and WebSocket flow
- ✓ Existing multi-agent cascade/swarm engine can generate persona-based deliberation and streamed messages — existing Simulation service
- ✓ Existing frontend can render a scenario input, live activity feed, interaction graph, detected conflicts, and report route — existing Next.js app
- ✓ Existing fallback behavior allows demo runs without all external services available — existing rule-based and stub paths
- ✓ Existing codebase map documents stack, architecture, conventions, integrations, testing, and concerns — mapped on 2026-05-09
- ✓ CivicBridge product shell and primary simulator intake are immigration-focused — Phase 1, completed 2026-05-09
- ✓ Founder Immigration and First 1000 Days tracks, guided scenarios, structured facts, uncertainty chips, and safety copy exist in the primary simulator — Phase 1, completed 2026-05-09

### Active

- [x] Rebrand the product from OrgSim to CivicBridge Simulator or an equivalent immigration-focused name.
- [x] Replace department/business language with two user-facing tracks: Founder Immigration and Learning to be American.
- [ ] Preserve and adapt the simulation workflow so users can run immigration or settlement scenarios through simulated advisor personas.
- [ ] Create immigration-domain personas, such as immigration attorney, founder mentor, employer/talent lead, evidence coach, tax/finance navigator, healthcare navigator, housing navigator, credit/banking navigator, and cultural systems mentor.
- [ ] Convert detected "conflicts" into user-centered risks, blockers, evidence gaps, tradeoffs, and timeline collisions.
- [ ] Produce an action-oriented report with next steps, uncertainty, "not legal advice" caveats, and when to consult a qualified professional.
- [x] Add guided demo scenarios that satisfy both hackathon tracks and work reliably without external credentials.
- [ ] Keep the implementation narrow enough for a hackathon: one polished combined flow beats many shallow feature stubs.

### Out of Scope

- Filing immigration forms or submitting applications — high legal/compliance risk and not required for a helpful simulator.
- Guaranteeing visa eligibility, approval odds, processing times, or legal outcomes — immigration facts change and individual cases require professional review.
- Replacing lawyers, tax professionals, doctors, or licensed advisors — the app should help users prepare and ask better questions, not act as counsel.
- Building a full document management vault — useful later, but v1 should focus on scenario rehearsal and action planning.
- Building a native mobile app — web-first is sufficient for the hackathon.
- Rebuilding the entire TypeDB/Neo4j knowledge architecture before the demo — repurpose the current simulation path first, then deepen graph modeling if time allows.

## Context

The starting point is `ORG - SIM`, an organizational decision rehearsal engine. It already has a Python/FastAPI backend, a separate Python simulation service, a Next.js frontend, Docker-managed infrastructure, and local/cloud LLM fallback paths.

The reusable spine is:

1. Scenario input in `Frontend/app/simulate/page.tsx`
2. Run creation in `Backend/api/routes/simulate.py`
3. Persona generation and streamed deliberation in `Simulation/app.py`
4. Cascade/swarm engines in `Simulation/orgsim_engine/`
5. Conflict extraction in `Simulation/conflict/extractor.py`
6. WebSocket delivery through `Backend/api/ws/simulation.py`
7. Live feed, graph, and report surfaces in the frontend

The hackathon prompt has two tracks. The product should deliberately satisfy both:

- Founder Immigration: O-1, EB-1A, H-1B alternatives, company formation, cross-border ops, and stay-in-the-US strategy.
- Learning to be American: first-1000-days onboarding across banking, credit, healthcare, housing, taxes, and cultural/system navigation.

The project should be emotionally and practically useful. The user should feel less alone in a confusing system, but the app must be careful not to overclaim legal authority.

## Constraints

- **Brownfield codebase**: Build within the existing OrgSim architecture and avoid broad rewrites unless they directly enable the demo.
- **Hackathon timeline**: Prioritize a coherent end-to-end demo over complete platform generality.
- **Legal safety**: Output must include uncertainty, caveats, and professional-review guidance; it must not present legal conclusions as guaranteed advice.
- **Demo reliability**: Core demo should work with rule-based/local fallback paths even without cloud keys or every Docker service running.
- **Frontend ergonomics**: The first screen should be the actual tool, not a marketing landing page.
- **Source freshness**: Any legal or timeline claims should be framed cautiously unless backed by a source strategy; avoid brittle live claims in v1 if official-source retrieval is not implemented.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build a combined two-track product | User selected combined demo to satisfy both hackathon tracks | Implemented in Phase 1 intake |
| Reuse OrgSim simulation engine | Existing code already supports live multi-agent scenario rehearsal | Preserved through frontend compatibility shim |
| Treat conflicts as risks/blockers | Immigration users need actionable risk framing more than adversarial business conflict framing | Begun in Phase 1 UI; backend/domain conversion continues in Phases 2-3 |
| Keep v1 web-first | Existing Next.js app can be repurposed fastest | Confirmed by Phase 1 `/simulate` primary flow |
| Include legal-safety caveats in output | Immigration support must avoid pretending to replace qualified counsel | Phase 1 safety note added before run |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check -- still the right priority?
3. Audit Out of Scope -- reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-09 after Phase 1 execution*

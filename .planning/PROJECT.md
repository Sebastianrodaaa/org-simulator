# CivicBridge Simulator

## What This Is

CivicBridge Simulator repurposes OrgSim into a combined immigration and first-1000-days strategy tool. The **v1.0** hackathon release ships two tracks (Founder Immigration and Learning to be American), live multi-agent rehearsal with CivicBridge personas, risk-oriented UX, an action report with safety caveats, and reliable **GET** report hydration even on the backend stub and WebSocket mock paths.

## Core Value

Help immigrants and immigrant founders rehearse a complex life or visa decision before acting, surfacing risks, missing evidence, timeline collisions, and next steps in plain language.

## Current state (after v1.0)

| Area | Notes |
|------|--------|
| **Stack** | FastAPI backend, Python Simulation service (port 8001), Next.js frontend (submodule), optional Docker/Neo4j/NATS |
| **Demo** | `cd Backend && uvicorn api.main:app --reload --port 8000`; optional `Simulation` on 8001; `cd Frontend && npm run dev` |
| **Tests** | `pytest Simulation/tests`, `pytest Backend/tests/test_stub_snapshot.py`; full e2e when API is running |

## Requirements

### Validated (v1.0)

- ✓ CivicBridge shell, two tracks, guided scenarios, structured intake, uncertainty chips, pre-run safety copy — Phases 1–6
- ✓ Track-aware immigration / systems-navigation personas end-to-end — Phase 2
- ✓ Risks/blockers framing, categories, report sections, official-source links in report template — Phases 3, 5
- ✓ Stub + WS paths populate `messages` / `conflicts` / `report` on `GET /simulate/{id}` — Phase 5
- ✓ Automated tests (extractor, stub snapshot, e2e fixtures) and frontend lint/build — Phases 4, 6
- ✓ Full v1 REQ traceability — see [milestones/v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

### Active

_Define via `/gsd-new-milestone` (e.g. evidence workspace, saved scenarios, runtime source retrieval)._

### Out of Scope

Unchanged from v1 planning: filing forms, guaranteeing outcomes, replacing licensed professionals, full document vault, native mobile app, full immigration ontology rebuild, unrestricted legal web search in v1.

## Context

Brownfield OrgSim codebase: scenario input → `POST /simulate` → Simulation streaming → WebSocket → report route. Frontend may live in a **git submodule**; pin and push both repos for demos.

## Constraints

- Legal safety: no guaranteed eligibility or outcome language; professional-review prompts stay visible.
- Demo reliability: stub and mock paths remain first-class for judges without every service running.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Combined two-track product | Hackathon asks for both founder and settlement angles | Shipped v1.0 |
| Reuse OrgSim engine | Fastest path to multi-agent rehearsal | Shipped |
| Risks vs business “conflicts” | User-centered immigration framing | Shipped in UI + extractor metadata |
| `attach_snapshot_to_run` on all completion paths | Report route must work without only-live-demo | Shipped Phase 5 |
| Frontend submodule | Existing repo layout | Document for releases |

## Next milestone goals

- Run `/gsd-new-milestone` to capture priorities (e.g. SRC-/EVID-/PERS- items from the old v2 wishlist).

## Evolution

This document is updated at milestone boundaries. **Last structural pass:** v1.0 completion, 2026-05-09.

---
*Last updated: 2026-05-09 after v1.0 milestone completion*

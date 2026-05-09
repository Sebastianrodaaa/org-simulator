# Research: Architecture

**Date:** 2026-05-09
**Project:** CivicBridge Simulator
**Research dimension:** Architecture

## Recommended Architecture

Repurpose the existing OrgSim architecture by swapping domain vocabulary and data contracts, not by rebuilding the system.

```text
Scenario Intake
  -> Track + facts + uncertainties
  -> Advisor persona generation
  -> Swarm/cascade deliberation
  -> Risk extraction
  -> Live feed + risk graph
  -> Action report
```

## Component Boundaries

### Frontend

- Track selector and guided scenario templates.
- Intake form with freeform mode.
- Live advisor activity feed.
- Risk/dependency graph.
- Action report page.

Primary files:

- `Frontend/app/simulate/page.tsx`
- `Frontend/lib/types.ts`
- `Frontend/lib/api.ts`
- `Frontend/lib/wireSimulationEvents.ts`
- `Frontend/components/SwarmInteractionGraph.tsx`
- `Frontend/components/ConflictGraph.tsx`

### Backend API

- Validate track/persona/risk category inputs.
- Create run records.
- Bridge to simulation service.
- Store recent event history long enough for report viewing.

Primary files:

- `Backend/api/routes/simulate.py`
- `Backend/api/services/live_simulation.py`
- `Backend/api/run_store.py`
- `Backend/api/ws/simulation.py`

### Simulation Service

- Load domain templates.
- Build advisor personas.
- Execute deliberation.
- Extract risks and blockers.
- Emit complete summary.

Primary files:

- `Simulation/app.py`
- `Simulation/config_loader.py`
- `Simulation/org_persona_generator.py`
- `Simulation/swarm/persona_pool.py`
- `Simulation/orgsim_engine/decision_cascade.py`
- `Simulation/orgsim_engine/swarm_cascade.py`
- `Simulation/conflict/extractor.py`

### Knowledge/Source Layer

For v1, use curated static official-source metadata and seed content. Later, TypeDB can model pathways, dependencies, and evidence requirements.

Candidate graph nodes:

- person status
- goal
- pathway
- evidence item
- deadline
- dependency
- risk
- local/state factor
- professional review trigger

## Data Flow Changes

- `departments` becomes `advisors` or `perspectives`.
- `decision` becomes `scenario`.
- `conflict` becomes `risk`.
- `dept_a`/`dept_b` becomes `source_perspective`/`affected_area`.
- `recommendation` becomes `action_plan_summary`.

## Build Order

1. Add domain config and labels.
2. Convert frontend copy and demo scenarios.
3. Replace backend validation labels.
4. Replace persona templates.
5. Replace risk extraction heuristics.
6. Persist enough event/report data for the report page.
7. Add tests for new labels and risk categories.

## Sources

- Existing codebase map: `.planning/codebase/ARCHITECTURE.md`
- USCIS, International Entrepreneur Rule: https://www.uscis.gov/working-in-the-united-states/international-entrepreneur-rule
- HealthCare.gov, Lawfully present immigrants: https://www.healthcare.gov/immigrants/lawfully-present-immigrants/


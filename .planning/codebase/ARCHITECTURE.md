# Codebase Architecture

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## Architectural Shape

OrgSim is a two-service simulation system with a Next.js client:

1. The frontend collects a decision scenario and selected stakeholder groups.
2. The backend API creates and tracks simulation runs.
3. The backend calls the simulation service for persona generation and live event streaming.
4. The simulation service runs a cascade or swarm deliberation.
5. Conflicts are extracted from agent messages.
6. The frontend renders live feed, graph, and report surfaces.

This shape maps well to the immigration hackathon: "decision scenario" can become an immigration or settlement scenario, "departments" can become advisors/systems/actors, and "conflicts" can become risks, blockers, evidence gaps, timeline collisions, or onboarding dependencies.

## Primary Runtime Flow

The main live flow is:

- `Frontend/app/simulate/page.tsx`
- `Frontend/lib/api.ts`
- `Backend/api/routes/simulate.py`
- `Backend/api/services/live_simulation.py`
- `Simulation/app.py`
- `Simulation/org_persona_generator.py`
- `Simulation/orgsim_engine/swarm_cascade.py` or `Simulation/orgsim_engine/decision_cascade.py`
- `Simulation/conflict/extractor.py`
- `Backend/api/ws/simulation.py`
- `Frontend/lib/useSimulationStream.ts`
- `Frontend/lib/wireSimulationEvents.ts`

## API Layer

- `Backend/api/main.py` creates the FastAPI app, configures CORS, connects optional NATS/Temporal clients, and registers routers.
- `Backend/api/routes/simulate.py` validates simulation requests, creates run state, schedules background work, and exposes run lookup.
- `Backend/api/routes/health.py` checks TypeDB, Neo4j, and NATS connectivity.
- `Backend/api/run_store.py` is an in-memory store for run metadata, event queues, and reconnect history.

The API layer is intentionally thin; most domain behavior lives in the simulation service.

## Simulation Layer

- `Simulation/app.py` exposes persona generation, simulation execution, conflict extraction, report generation, streaming, and health endpoints.
- `Simulation/org_persona_generator.py` builds base personas from YAML templates and seed markdown reports.
- `Simulation/swarm/persona_pool.py` expands selected template roles into large synthetic swarms.
- `Simulation/orgsim_engine/decision_cascade.py` models a shared deliberation thread where every selected persona acts each round.
- `Simulation/orgsim_engine/swarm_cascade.py` models a large pool where a subset speaks each round.
- `Simulation/conflict/extractor.py` classifies cross-stakeholder conflicts.
- `Simulation/report_agent.py` generates summary reports.

## Data/Knowledge Layer

- `Backend/schema/orgsim.tql` defines TypeDB schema.
- `Backend/loaders/*.py` load mock business data from `infra/mock/`.
- `Backend/loaders/entity_resolver.py` creates dependency relations.
- `Backend/seed_reports/generator.py` converts graph data into department-specific markdown seed reports.
- `Backend/output/*_seed.md` is consumed by persona generation.
- `Simulation/cascade/tracer.py` queries dependencies and falls back to static dependencies if TypeDB is unavailable.

The current design uses markdown seed reports as a practical boundary between structured graph data and LLM/persona prompts.

## Frontend Layer

- `Frontend/app/dashboard/page.tsx` displays static org health, office/globe data, and a call to start a simulation.
- `Frontend/app/simulate/page.tsx` is the main interactive simulation surface.
- `Frontend/app/report/[id]/page.tsx` displays run/report details, though the backend currently returns only the basic run object for `GET /simulate/{run_id}`.
- `Frontend/components/SwarmInteractionGraph.tsx` visualizes agent interactions from event streams.
- `Frontend/components/ConflictGraph.tsx` visualizes conflicts and messages.
- `Frontend/components/ui/agent-plan.tsx` renders the activity feed.

## Domain Boundaries

Current domain labels are business-org-specific:

- Departments: Sales, Finance, Operations, HR, Engineering, Marketing.
- Personas: CFO, VP Sales, Ops Lead, HR Director.
- Conflicts: resource, priority, timeline, budget.
- Metrics: pipeline, quota, runway, capacity, attrition.

For the repurpose, these labels should become immigration-system-specific while preserving the same architectural slots:

- Pathways/advisors instead of departments.
- Applicant, founder, lawyer, employer, officer, banker, healthcare navigator, tax advisor, landlord, or mentor personas instead of org executives.
- Risks such as eligibility, evidence, timing, cost, compliance, housing, healthcare, credit, tax, and work authorization instead of business conflicts.
- A personal timeline and case facts instead of company metrics.

## Recommended Build Order For Repurpose

1. Rename product copy and frontend flows while preserving route structure.
2. Replace department/persona config with immigration tracks and advisor personas.
3. Replace seed reports with immigration/settlement knowledge cards.
4. Replace conflict categories and extraction heuristics with risk/blocker categories.
5. Add structured scenario intake for Founder Immigration and Learning to be American.
6. Add timeline/report features that convert simulation output into next actions and caveats.


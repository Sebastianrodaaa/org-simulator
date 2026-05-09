# Codebase Structure

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## Root

- `README.md` documents the OrgSim demo, architecture, quick start, and test commands.
- `docker-compose.yml` defines TypeDB, Neo4j, NATS, Temporal, Ollama, and simulation services.
- `requirements.txt` defines Python dependencies shared by backend and simulation.
- `infra/config.yaml` defines valid departments and simulation tuning.
- `infra/mock/` contains synthetic business data used by loaders.
- `tasks.md` appears to be project task notes.
- `CLAUDE.md` contains previous assistant/project instructions.
- `.planning/handoff.md` exists from prior planning work.

## Backend Directory

- `Backend/api/main.py` is the API entry point.
- `Backend/api/routes/health.py` implements `GET /health`.
- `Backend/api/routes/simulate.py` implements `POST /simulate` and `GET /simulate/{run_id}`.
- `Backend/api/ws/simulation.py` implements the WebSocket endpoint.
- `Backend/api/services/live_simulation.py` bridges the API to the simulation service.
- `Backend/api/run_store.py` stores in-memory run data.
- `Backend/api/nats_client.py` and `Backend/api/temporal/` hold optional infra clients.
- `Backend/schema/orgsim.tql` defines TypeDB types.
- `Backend/schema/init_db.py` creates/loads the TypeDB database.
- `Backend/loaders/` contains ETL loaders and dependency resolution.
- `Backend/seed_reports/generator.py` writes markdown seed reports.
- `Backend/output/` contains generated seed report markdown.
- `Backend/demo/seed_demo.py` drives a demo run.
- `Backend/tests/` contains API/schema/e2e tests.

## Simulation Directory

- `Simulation/app.py` is the simulation HTTP service entry point.
- `Simulation/config_loader.py` reads runtime config.
- `Simulation/org_persona_generator.py` builds base personas.
- `Simulation/report_agent.py` creates final reports.
- `Simulation/templates/*.yaml` defines current org persona templates.
- `Simulation/orgsim_engine/decision_cascade.py` contains the full-participant deliberation engine.
- `Simulation/orgsim_engine/swarm_cascade.py` contains the sampled-swarm deliberation engine.
- `Simulation/swarm/persona_pool.py` expands template personas into large pools.
- `Simulation/cascade/tracer.py` builds dependency/cascade maps from TypeDB or fallback data.
- `Simulation/conflict/extractor.py` detects and classifies conflicts.
- `Simulation/tests/` contains unit tests for persona and swarm behavior.
- `Simulation/mirofish/` is a bundled/adapted upstream simulation project and should be treated as a large vendor/reference subtree unless explicitly changed.

## Frontend Directory

- `Frontend/app/layout.tsx` wraps pages and likely renders navigation.
- `Frontend/app/page.tsx` redirects to `/dashboard`.
- `Frontend/app/dashboard/page.tsx` renders current org-health dashboard.
- `Frontend/app/simulate/page.tsx` renders the main simulation UI.
- `Frontend/app/report/[id]/page.tsx` renders a report/detail page.
- `Frontend/app/globals.css` contains global Tailwind/CSS.
- `Frontend/components/Nav.tsx` defines top navigation.
- `Frontend/components/ConflictGraph.tsx` visualizes conflict relationships.
- `Frontend/components/SwarmInteractionGraph.tsx` visualizes streamed agent interactions.
- `Frontend/components/DeptFeedDrawer.tsx` renders department details.
- `Frontend/components/ui/agent-plan.tsx` renders a compact activity plan/feed.
- `Frontend/components/ui/cobe-globe.tsx` renders the dashboard globe.
- `Frontend/lib/api.ts` contains API calls.
- `Frontend/lib/types.ts` contains shared frontend types.
- `Frontend/lib/useSimulationStream.ts` handles the run WebSocket.
- `Frontend/lib/wireSimulationEvents.ts` normalizes wire events.

## Naming Conventions

- Backend and Simulation directories are capitalized (`Backend`, `Simulation`), while some README/test comments mention lowercase paths.
- Python files use snake_case modules and functions.
- Frontend components use PascalCase filenames and exported components.
- Frontend hooks use `use*` naming.
- Current domain names are baked into constants such as `ALL_DEPTS`, `DEPT_COLOR`, and `DEMO_DECISION` in `Frontend/app/simulate/page.tsx`.

## Files Most Relevant To Immigration Repurpose

- `Frontend/app/simulate/page.tsx`: main UI conversion point.
- `Frontend/app/dashboard/page.tsx`: can become an immigrant/founder command center.
- `Frontend/app/report/[id]/page.tsx`: can become action plan, timeline, evidence gaps, and caveat report.
- `Frontend/lib/types.ts`: rename domain types from departments/conflicts to tracks/risks.
- `Backend/api/routes/simulate.py`: validate new participant/track labels.
- `infra/config.yaml`: define new track/persona template mapping.
- `Simulation/templates/*.yaml`: replace org roles with immigration/system-navigation personas.
- `Simulation/org_persona_generator.py`: replace seed report semantics.
- `Simulation/conflict/extractor.py`: replace business conflict heuristics with immigration risk/blocker heuristics.
- `Backend/schema/orgsim.tql` and loaders: repurpose graph data if the project needs structured pathway reasoning.


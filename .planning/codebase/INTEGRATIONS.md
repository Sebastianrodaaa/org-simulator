# Codebase Integrations

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## Overview

The application is integration-heavy but designed to degrade gracefully. The core demo can run with local services and rule-based fallback behavior, while graph, LLM, and event infrastructure enrich the result when available.

## Browser To API

- `Frontend/lib/api.ts` calls the public API at `NEXT_PUBLIC_API_URL` or `http://localhost:8000`.
- `startSimulation()` posts to `POST /simulate`.
- `getSimulation()` polls `GET /simulate/{run_id}`.
- `getHealth()` calls `GET /health`.
- `Frontend/lib/useSimulationStream.ts` opens `ws://.../ws/simulation/{run_id}` for live events.

## API To Simulation Service

- `Backend/api/services/live_simulation.py` resolves a simulation service URL.
- If `SIMULATION_SERVICE_URL` is configured, the API uses it.
- If not configured, it probes `http://127.0.0.1:8001/health`.
- If the simulation service is unavailable, `Backend/api/routes/simulate.py` falls back to `_stub_run()`.
- Live runs call `POST /generate-personas`, then stream `POST /stream-simulation` NDJSON.

## WebSocket Event Stream

- `Backend/api/ws/simulation.py` owns WebSocket delivery.
- `Backend/api/run_store.py` holds in-memory run state, per-run queues, and event history.
- Events are sent as `agent_message`, `conflict`, `complete`, or `error`.
- `Frontend/lib/wireSimulationEvents.ts` normalizes flat mock/simulation events and nested NATS-style events into UI types.

## NATS

- The simulation service optionally publishes events to NATS via `_publish()` in `Simulation/app.py`.
- Subjects use `orgsim.simulation.{run_id}.agent` and `orgsim.simulation.{run_id}.conflict`.
- The current API streaming path does not require NATS; it reads NDJSON directly from the simulation service.
- This is useful for the hackathon because the live UI can work without standing up every infra component.

## Temporal

- `Backend/api/main.py` attempts to connect to Temporal at startup through `api.temporal.client`.
- The current live simulation route does not appear to depend on Temporal for the main local demo path.
- Temporal can likely be deferred during the immigration repurpose unless multi-step background workflows become essential.

## TypeDB

- `Backend/schema/orgsim.tql` defines organization entities, metrics, budgets, deals, and `CrossDeptDependency`.
- `Backend/schema/init_db.py` initializes the database and schema.
- `Backend/loaders/*.py` populate mock data from `infra/mock/`.
- `Simulation/cascade/tracer.py` queries TypeDB for dependency traversal and falls back to a static dependency map if TypeDB is unavailable.
- For immigration, TypeDB is the natural place to model visa pathways, eligibility evidence, deadlines, dependencies, risk factors, and "first 1000 days" systems.

## Neo4j

- Neo4j is declared in `docker-compose.yml` and checked by `Backend/api/routes/health.py`.
- The root path also includes an embedded `Simulation/mirofish/` app with Neo4j-oriented services.
- The main OrgSim API path does not appear to rely deeply on Neo4j yet.
- For hackathon scope, Neo4j should be treated as optional unless graph visualization or memory from `Simulation/mirofish` is explicitly reused.

## Ollama And OpenAI-Compatible LLMs

- `Simulation/org_persona_generator.py` uses DSPy and can target local Ollama by default.
- `Simulation/orgsim_engine/decision_cascade.py` uses the OpenAI SDK either against OpenAI or Ollama's OpenAI-compatible endpoint.
- Fallback rule-based persona and action generation is present when LLM setup fails.
- `Simulation/conflict/extractor.py` and `Simulation/report_agent.py` also attempt DSPy/OpenAI paths with fallback behavior.

## Tavily

- `Simulation/org_persona_generator.py` can enrich persona seed context through Tavily.
- `Simulation/report_agent.py` also references Tavily for market-style research enrichment.
- For immigration, Tavily-style external search must be handled carefully: use official sources for legal/timeline claims and label non-legal guidance clearly.

## Known Integration Risks

- Credentials/defaults are hardcoded for local dev in `docker-compose.yml`, `Backend/api/routes/health.py`, and TypeDB helpers.
- The API CORS allowlist in `Backend/api/main.py` is fixed to `http://localhost:3000`.
- Some docs and tests reference `backend/` lowercase while the repo path is `Backend/`.
- The simulation service imports modules as local top-level modules, so working directory and `PYTHONPATH` matter.


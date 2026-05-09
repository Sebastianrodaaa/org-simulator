# Codebase Stack

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## Overview

OrgSim is a multi-service local simulation product. The current stack combines a Python/FastAPI backend, a separate Python simulation service, a Next.js frontend, and Docker-managed infrastructure for graph storage, workflow/eventing, and local LLM execution.

For the immigration hackathon repurpose, the most reusable stack element is the simulation pipeline: a user submits a scenario, personas deliberate, conflicts are extracted, and the browser receives a live stream of reasoning events.

## Languages And Runtimes

- Python 3.11/3.12 is the expected backend/runtime target, documented in `README.md`.
- TypeScript is used in the frontend under `Frontend/`.
- Node.js 20+ is expected for frontend development.
- Docker Compose orchestrates local infrastructure from `docker-compose.yml`.

## Python Services

- `Backend/api/main.py` defines the public FastAPI API on port 8000.
- `Simulation/app.py` defines the simulation FastAPI service on port 8001.
- `Backend/loaders/run_all.py` initializes TypeDB data and generates seed reports.
- `Simulation/org_persona_generator.py` creates persona records from YAML templates and seed report markdown.
- `Simulation/orgsim_engine/decision_cascade.py` and `Simulation/orgsim_engine/swarm_cascade.py` run the deliberation engines.

## Python Dependencies

Declared in `requirements.txt`:

- API/runtime: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `httpx`, `python-multipart`, `python-dotenv`.
- Graph/data: `typedb-driver`, `neo4j`, `pandas`, `PyYAML`.
- Event/workflow: `nats-py`, `temporalio`.
- LLM and research: `dspy-ai`, `openai`, `tavily-python`.
- Tests: `pytest`, `pytest-asyncio`.

## Frontend Stack

Declared in `Frontend/package.json`:

- Next.js `16.2.3` App Router with React `19.2.4`.
- TypeScript `^5`.
- Tailwind CSS v4 via `@tailwindcss/postcss`.
- Visualization and motion: `d3`, `cobe`, `framer-motion`.
- Icons: `lucide-react`.
- Data fetching helper: `swr`, though current simulation paths mostly use native `fetch` and WebSocket.

## Infrastructure

Defined in `docker-compose.yml`:

- TypeDB `3.3.0` on port 1729.
- Neo4j `5.15-community` on ports 7474/7687.
- NATS `2.10-alpine` with JetStream on ports 4222/8222.
- Temporal auto-setup `1.24` on port 7233.
- Ollama on port 11434.
- Simulation container built from `Simulation/Dockerfile`.

## Configuration

- `infra/config.yaml` contains valid department labels and simulation tuning.
- `Simulation/config_loader.py` reads `ORGSIM_CONFIG` or defaults to `infra/config.yaml`.
- Runtime LLM behavior is configured through environment variables such as `LLM_MODEL_NAME`, `OLLAMA_HOST`, `OLLAMA_BASE_URL`, `OPENAI_API_KEY`, and `ORGSIM_USE_CLOUD_OPENAI`.
- API-to-simulation communication uses `SIMULATION_SERVICE_URL` when set, otherwise probes `http://127.0.0.1:8001`.

## Build And Run Commands

- Start infrastructure: `docker compose up -d`.
- Load graph data and seed reports: `cd Backend && TYPEDB_INIT_DROP=1 python -m loaders.run_all`.
- Start API: `cd Backend && uvicorn api.main:app --reload --port 8000`.
- Start simulation service: `cd Simulation && uvicorn app:app --reload --port 8001`.
- Start frontend: `cd Frontend && npm run dev`.
- Frontend build/lint: `cd Frontend && npm run build` and `cd Frontend && npm run lint`.

## Repurpose Notes

- The current stack is heavy for a hackathon demo, but already supports a compelling live simulation UX.
- TypeDB can be repurposed from org dependencies into immigration pathways, evidence categories, deadlines, constraints, and life-system dependencies.
- The frontend already has a scenario simulator screen, live agent feed, conflict graph, and report route. Those should be re-skinned and relabeled rather than rebuilt from scratch.
- The local LLM fallback rules are useful for demo reliability when Ollama or cloud keys are unavailable.


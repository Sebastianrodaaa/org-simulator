# OrgSim — Organizational Decision Rehearsal Engine

## What this project is
OrgSim unifies departmental data silos (Sales, Finance, Ops, HR) into a shared
TypeDB ontology, then runs a forked MiroFish swarm simulation engine where agents
are internal org stakeholders (CFO, VP Sales, Ops Lead, HR Director) instead of
public personas. The goal: simulate the cascade of a business decision BEFORE it
is made. This is decision rehearsal, not task automation.

## The novel thesis
Existing tools (WatsonX, Palantir AIP) automate or surface existing workflows.
OrgSim simulates proposed decisions forward in time, surfacing emergent cross-dept
conflicts that only exist in the *interaction* between datasets — not in any
single dataset alone.

## Tech stack
- TypeDB + TypeQL: cross-department ontology and relationship graph
- MiroFish-Offline fork (nikmcfly/MiroFish-Offline): swarm sim engine (Neo4j + Ollama)
- Neo4j: agent memory and entity relationship graph inside MiroFish
- Temporal.io: durable, checkpointed workflow orchestration for simulation runs
- NATS JetStream: real-time event streaming from sim engine to frontend
- FastAPI: REST + WebSocket API layer (Python 3.11+)
- Next.js 15 App Router + Tailwind: frontend dashboard
- Ollama (qwen2.5:32b or qwen2.5:14b): local LLM — NO cloud API calls
- DSPy: compile agent reasoning pipelines instead of writing raw prompts
- Cedar (optional, Phase 3+): policy enforcement for scenario authorization

## Key constraints
- Everything runs locally — zero cloud LLM dependencies
- Simulation must complete a demo run in under 90 seconds
- Agents must have role-specific behavioral biases in persona templates
- The "CFO cuts Q4 marketing budget 20%" scenario is the primary demo — build toward it

## File structure
```
orgsim/
├── CLAUDE.md              # this file — loaded automatically by Claude Code
├── tasks.md               # agent coordination — read before starting any task
├── .cursorrules           # Cursor IDE context
├── docker-compose.yml     # all services
├── backend/
│   ├── schema/            # TypeDB .tql schema files
│   ├── loaders/           # ETL: CSV/JSON/YAML → TypeDB
│   ├── api/               # FastAPI routes and WebSocket handlers
│   ├── seed_reports/      # dept-specific markdown seed report generators
│   └── tests/
├── simulation/
│   ├── mirofish/          # cloned + adapted MiroFish-Offline fork
│   ├── templates/         # org role persona templates (CFO, VP Sales, etc.)
│   ├── conflict/          # conflict extractor from agent interaction logs
│   └── cascade/           # TypeDB traversal → cascade impact mapper
├── frontend/              # Next.js 15 app
└── infra/
    ├── mock/              # mock dept data: sales_pipeline.csv, finance_pl.json, ops_capacity.yaml
    └── docker/            # per-service Dockerfiles if needed
```

## Agent coordination protocol
- Always read tasks.md before starting any task
- Mark tasks [~] when starting, [x] when done, [!] if blocked with reason
- Do not modify files marked [~] by another agent — coordinate via tasks.md
- When a phase completes, update tasks.md and confirm output artifacts exist

## Code conventions
- Python: 3.11+, type hints everywhere, pydantic models for all data shapes
- No print() for logging — use Python logging module with named loggers
- FastAPI: async handlers only, use dependency injection for DB clients
- TypeDB: all queries in backend/schema/*.tql files, never inline strings
- Frontend: TypeScript strict mode, no `any`, use SWR for data fetching
- Commit messages: conventional commits (feat:, fix:, chore:, docs:)

## What NOT to do
- Do not use cloud LLM APIs (OpenAI, Anthropic direct) — use Ollama only
- Do not use the Next.js pages/ router — App Router only
- Do not write raw prompt strings for agent reasoning — use DSPy signatures
- Do not install TypeDB driver v2.x — use typedb-driver 3.x (breaking API change)
- Do not hardcode dept names — they must be configurable via infra/config.yaml

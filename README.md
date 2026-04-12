# OrgSim — Organizational Decision Rehearsal Engine

> Simulate business decisions before you make them.

OrgSim unifies departmental data silos into a shared knowledge graph, then runs
a swarm of AI agents representing internal stakeholders to predict cross-department
cascade effects of any proposed decision.

## What's novel
Existing enterprise AI tools (WatsonX, Palantir AIP) automate or surface existing
workflows. OrgSim simulates *proposed* decisions forward in time — surfacing emergent
conflicts that only exist in the interaction between departments, not in any single
dataset alone.

## Architecture
```
[Dept Data Silos] → [TypeDB Ontology] → [Seed Reports] → [MiroFish Swarm Engine]
                                                                    ↓
[Next.js Dashboard] ← [NATS Stream] ← [Temporal Workflow] ← [Conflict Extractor]
```

## Quick start (~8 minutes)

### Prerequisites
- Docker Desktop (running)
- Python 3.11+
- Node.js 20+
- 16 GB RAM (for local LLM)

### 1. Start infrastructure (~2 min)
```bash
cd /path/to/orgsim          # e.g. cd ~/Desktop/26
docker compose up -d
docker compose ps           # all 5 services should show healthy/running
```

### 2. Pull the local LLM (~3 min, one-time)
Run **one** of these from the same directory as `docker-compose.yml` (keep `docker exec … ollama pull` on a single line — a line break after `orgsim-ollama` will fail):

```bash
docker compose exec ollama ollama pull qwen2.5:14b
docker compose exec ollama ollama list            # verify model listed
```

Equivalent using the container name:

```bash
docker exec orgsim-ollama ollama pull qwen2.5:14b
docker exec orgsim-ollama ollama list
```

### 3. Python environment
Use **Python 3.11 or 3.12** (3.14+ may lack wheels and fail on `pip install`). From the project root:

```bash
cd /path/to/orgsim                      # project root
python3.11 -m venv .venv                # or: python3.12 -m venv .venv
source .venv/bin/activate               # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Load mock data + generate seed reports
With the venv **activated** (or using `.venv/bin/python`):

```bash
cd Backend
TYPEDB_INIT_DROP=1 python -m loaders.run_all   # first run or after schema changes (wipes orgsim DB)
# python -m loaders.run_all                     # later: only if DB empty or you use upserts (default may fail on duplicate inserts)
# Expect: "All steps completed successfully."
# Creates: Backend/output/*_seed.md
```

### 5. Start the API
```bash
# From backend/
uvicorn api.main:app --reload --port 8000
# Expect: "OrgSim API starting up..."
# Health: curl http://localhost:8000/health
```

### 6. Start the frontend
```bash
cd frontend
npm install
npm run dev
# Open: http://localhost:3000
```

### 7. Run the demo scenario
```bash
# With API running, in a new terminal:
cd backend
python -m demo.seed_demo
# Prints run_id, conflicts, recommendation, report URL
# Should complete in < 90 seconds
```

## Demo scenario
Navigate to http://localhost:3000/simulate and enter:
> "The CFO has decided to cut the Q4 marketing budget by 20%. Simulate the
> organizational cascade over the next 90 days."

Select departments: Sales, Finance, Operations, HR → Submit

Watch live agent debate stream → conflict graph populates → report generated.

## Key files
```
backend/
  api/main.py              FastAPI app (port 8000)
  api/routes/simulate.py   POST/GET /simulate
  api/ws/simulation.py     WebSocket stream
  api/temporal/workflow.py OrgSimWorkflow + 4 activities
  api/nats_client.py       JetStream ORGSIM stream
  demo/seed_demo.py        Demo pre-seeder / acceptance test
  schema/orgsim.tql        TypeDB ontology
  loaders/run_all.py       Full ETL pipeline
frontend/
  app/simulate/page.tsx    Scenario input + live agent feed
  app/dashboard/page.tsx   Dept health overview
  app/report/[id]/page.tsx Decision report viewer
infra/mock/                Synthetic dept data (CSV/JSON/YAML)
```

## Tech stack
TypeDB 3.x · MiroFish-Offline · Neo4j 5 · Temporal.io · NATS JetStream ·
FastAPI · Next.js 15 App Router · Ollama (qwen2.5:14b) · DSPy

## Running tests
```bash
# Unit / schema tests (requires TypeDB running + loaders executed):
cd backend && pytest tests/test_schema.py -v

# End-to-end (requires all services + API running):
pytest tests/test_e2e.py -v -m e2e
```

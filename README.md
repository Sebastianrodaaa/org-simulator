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

## Quick start

### Prerequisites
- Docker + Docker Compose
- Python 3.11+
- Node.js 20+
- 16GB+ RAM (for local LLM)

### 1. Clone and configure
```bash
git clone https://github.com/YOUR_USERNAME/orgsim.git
cd orgsim
cp .env.example .env
```

### 2. Start all services
```bash
docker compose up -d
```

### 3. Pull the local LLM
```bash
docker exec orgsim-ollama ollama pull qwen2.5:14b
```

### 4. Install Python dependencies
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Load mock data
```bash
python -m loaders.run_all
```

### 6. Start the API
```bash
uvicorn api.main:app --reload
```

### 7. Start the frontend
```bash
cd frontend
npm install && npm run dev
```

Open http://localhost:3000

## Demo scenario
Navigate to `/simulate` and run:
> "The CFO has decided to cut the Q4 marketing budget by 20%. Simulate the
> organizational cascade over the next 90 days."

## Tech stack
TypeDB · MiroFish · Neo4j · Temporal.io · NATS JetStream · FastAPI · Next.js 15 · Ollama

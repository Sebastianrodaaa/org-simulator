# CivicBridge: Rehearsal for Immigration and First-1000-Days Decisions

Planning aid that runs a panel of simulated advisors over a situation you describe, then returns an action report: known facts, open uncertainties, items to verify, and questions for a qualified professional. This repository is the CivicBridge v1 hackathon release. It also keeps the OrgSim rehearsal engine it was built on: cascade and swarm rounds, a FastAPI run API, and a Next.js rehearsal UI.

CivicBridge starts from a structured intake (situation, key facts, uncertainty chips) and lets advisor personas deliberate in place. A founder run uses Immigration Attorney, Evidence Coach, Founder Mentor, and Tax / Company Navigator. A first-1000-days run uses Banking Navigator, Healthcare Navigator, Housing Navigator, Tax Navigator, and Local Systems Mentor. Events stream to the browser. When the run completes, `GET /simulate/{id}` hydrates the transcript and the report. The same loop still finishes when the optional graph services are down, and it falls back to rule-based personas when no model endpoint is reachable.

In this repo, the product surface is the rehearsal screen at `/simulate`. Advisor tracks are declared in `infra/config.yaml`. Persona text lives in `Simulation/templates/`. The run API is `Backend/api/routes/simulate.py`. The round engines are `Simulation/orgsim_engine/`.

![CivicBridge rehearsal screen with the founder demo prefilled](docs/civicbridge-rehearse.png)

**Note:** This repository was previously published as OrgSim, an organizational decision-rehearsal engine (department silos, CFO / VP Sales / Ops / HR personas, a "cut Q4 marketing 20%" demo). It has been retargeted. The department templates are still on disk as the legacy scaffold, and the repository now centers on CivicBridge. GitHub redirects the old project URL `0180150401/26` to [Sebastianrodaaa/org-simulator](https://github.com/Sebastianrodaaa/org-simulator).

## Table of Contents

- [Overview](#overview)
- [Rehearsal Loop](#rehearsal-loop)
- [Architecture](#architecture)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Requirements](#requirements)
- [Installation](#installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Python Environment](#2-python-environment)
  - [3. Frontend Dependencies](#3-frontend-dependencies)
  - [4. Optional Infrastructure](#4-optional-infrastructure)
- [Model Backend Setup](#model-backend-setup)
- [Running CivicBridge](#running-civicbridge)
- [API Fields](#api-fields)
- [Customizing Advisor Behavior](#customizing-advisor-behavior)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [Results](#results)

## Overview

This repo packages the CivicBridge v1 demo on top of the OrgSim multi-agent engine. It provides:

- **Founder rehearsal** — prefilled situation comparing O-1, EB-1A, and the International Entrepreneur Rule against company setup, evidence, dependents, and timing. The rehearsal screen sends `track: "founder"`.
- **First-1000-days panel** — banking, healthcare, housing, tax, and local-systems advisors, selected by sending `track: "first1000"` on `POST /simulate`. The on-screen demo does not switch tracks by itself.
- **Two engines** — `cascade` (the full panel speaks every round) and `swarm` (a larger pool; a subset speaks each round). The UI defaults to swarm, pool size 24, 8 active per round.
- **Action report** — executive summary, risks, recommended actions, grounded facts, open uncertainties, facts to verify, questions for a professional, official source links, and a planning-aid caveat.
- **Stub completion** — if the Simulation service on port 8001 is unreachable, the API still completes the run and attaches a snapshot so the report route can load.
- **Seven locales** — English, Spanish, French, Italian, Chinese, Japanese, and Russian (`Frontend/messages/`).

Eligibility, approval odds, and agency timelines are outside what this tool decides. The safety note on the rehearsal screen says so, and persona templates forbid guaranteeing an outcome.

## Rehearsal Loop

A run is one situation, one track, and one engine. The browser posts the scenario, opens a WebSocket, and renders advisor messages and the risk map as events arrive.

**What it does.**

1. Intake collects the situation, six key facts (current status, goal, deadline, location, work or company, family or dependents), and uncertainty chips. Empty facts are allowed. Selected chips are written into the scenario text.
2. The API creates a run and, when `http://127.0.0.1:8001/health` answers, calls the Simulation service.
3. The service builds personas from the track templates in `infra/config.yaml` and `Simulation/templates/*.yaml`.
4. Cascade or swarm runs the requested number of rounds and streams `agent_message` events. After the rounds, the conflict extractor emits risk-shaped events.
5. `attach_snapshot_to_run` writes `messages`, `conflicts`, and `report` onto the run so `GET /simulate/{id}` can serve the action report, including after a refresh.

**Running it.** Three processes. From the repo root, with the virtualenv active:

```bash
# API
cd Backend && uvicorn api.main:app --reload --port 8000

# Rehearsal engine
cd Simulation && uvicorn app:app --reload --port 8001

# UI
cd Frontend && npm run dev
```

Open [http://localhost:3000/simulate](http://localhost:3000/simulate). The founder situation is already filled in. Press **Run rehearsal**. When the risk map marks complete, open the action report.

Create a first-1000-days run directly:

```bash
curl -s -X POST http://127.0.0.1:8000/simulate \
  -H 'content-type: application/json' \
  -d '{
    "decision": "I arrived recently and need to sequence an identifier, a bank account, health coverage, housing, and taxes before a lease deadline.",
    "track": "first1000",
    "engine": "cascade",
    "rounds": 4
  }'
```

Then open `http://localhost:3000/report/<run_id>`.

The legacy department demo is still callable when `track` is omitted and `departments` is a subset of Sales, Finance, Operations, HR, Engineering, Marketing. That path uses the old CFO / VP Sales / Ops / HR templates. CivicBridge runs should send `track`.

## Architecture

The UI is a client of the API. The API is a client of the Simulation service. Optional services (TypeDB, Neo4j, NATS, Temporal, Ollama) are probed at startup and skipped when they refuse the connection.

Typical process layout:

- `Frontend` (`next dev`, port 3000) renders `/simulate`, `/dashboard`, and `/report/[id]`. It calls `POST /simulate` and subscribes to `/ws/simulation/{run_id}`.
- `Backend` (port 8000) stores the run in memory, relays stream events, and attaches the report snapshot.
- `Simulation` (port 8001) exposes `/generate-personas`, `/stream-simulation`, `/extract-conflicts`, `/generate-report`, and `/health`.
- The web app is the product UI. There is no separate stream page; the rehearsal screen is the live view.

```
[Next.js /simulate] -- POST /simulate --> [FastAPI :8000]
        |                                      |
        | WebSocket /ws/simulation/{id}        | NDJSON stream
        |                                      v
        +--------------------------- [Simulation :8001]
                                      personas → cascade | swarm → risks → report
```

Module map:

| Path | Role |
| --- | --- |
| `Backend/api/main.py` | FastAPI app, CORS for local Next.js ports, lifespan connects |
| `Backend/api/routes/simulate.py` | `POST /simulate`, `GET /simulate/{run_id}`, stub completion |
| `Backend/api/services/live_simulation.py` | Probes port 8001 and drives the streaming pipeline |
| `Backend/api/simulation_snapshot.py` | Builds the GET payload (messages, risks, report) |
| `Backend/api/ws/simulation.py` | WebSocket relay; optional scripted mock when `ORGSIM_ALLOW_MOCK_WEBSOCKET` is set |
| `Simulation/app.py` | Simulation HTTP service |
| `Simulation/orgsim_engine/decision_cascade.py` | Full-panel rounds |
| `Simulation/orgsim_engine/swarm_cascade.py` | Subset-of-pool rounds |
| `Simulation/conflict/extractor.py` | Risk pairs from the transcript |
| `Simulation/report_agent.py` | Report compilation |
| `infra/config.yaml` | Track → template ids, swarm defaults |

## Features

- **Two advisor tracks** in `infra/config.yaml`: `founder` and `first1000`.
- **Role-specific personas.** Each YAML template sets scope, forbidden actions (including outcome guarantees), and a behavioral bias. See `Simulation/templates/`.
- **Cascade and swarm** on both the API and the rehearsal screen.
- **Live activity trace and risk map** (`Frontend/components/ConflictGraph.tsx`, `SwarmInteractionGraph.tsx`).
- **Report that separates fact buckets:** grounded facts, open uncertainties, verify-before-acting, professional questions, source links, caveat.
- **Locale switcher** in the nav. Default locale is English; the prefix is omitted for `en`.
- **Demo without cloud keys.** Unreachable Ollama or a missing `OPENAI_API_KEY` falls through to rule-based persona text and round decisions.
- **Optional Docker stack** in `docker-compose.yml`: TypeDB 3.3, Neo4j 5, NATS JetStream, Temporal, Ollama, and the simulation image.
- **Tests:** `pytest Simulation/tests` (16 tests) and `pytest Backend/tests/test_stub_snapshot.py`.

## Directory Structure

```
org-simulator/
├── README.md
├── requirements.txt          # Python deps for Backend + Simulation
├── docker-compose.yml        # Optional TypeDB, Neo4j, NATS, Temporal, Ollama
├── infra/
│   ├── config.yaml           # Advisor tracks and swarm defaults
│   └── mock/                 # Legacy department fixtures (CSV / JSON / YAML)
├── Backend/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/simulate.py
│   │   ├── routes/health.py
│   │   ├── services/live_simulation.py
│   │   ├── simulation_snapshot.py
│   │   └── ws/simulation.py
│   ├── demo/seed_demo.py     # Legacy department demo seeder
│   ├── loaders/              # TypeDB loaders
│   ├── schema/
│   └── tests/
├── Simulation/
│   ├── app.py                # Port 8001
│   ├── org_persona_generator.py
│   ├── orgsim_engine/        # decision_cascade.py, swarm_cascade.py
│   ├── conflict/extractor.py
│   ├── report_agent.py
│   ├── templates/            # One YAML file per advisor
│   └── tests/
├── Frontend/
│   ├── app/[locale]/simulate/page.tsx
│   ├── app/[locale]/dashboard/page.tsx
│   ├── app/[locale]/report/[id]/page.tsx
│   ├── messages/             # en, es, fr, it, zh, ja, ru
│   └── lib/api.ts            # NEXT_PUBLIC_API_URL, default http://localhost:8000
└── docs/
    └── civicbridge-rehearse.png
```

## Requirements

- Python 3.11 or 3.12
- Node.js 20+
- A model endpoint only if you want generated persona text instead of the rule fallback (see [Model Backend Setup](#model-backend-setup))
- Docker Desktop only if you want TypeDB, Neo4j, NATS, Temporal, or containerized Ollama

The rehearsal screen, the API, and the Simulation service run without those containers.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Sebastianrodaaa/org-simulator
cd org-simulator
```

### 2. Python Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Use the activated environment for every `uvicorn` and `pytest` command below.

### 3. Frontend Dependencies

```bash
cd Frontend
npm install
```

### 4. Optional Infrastructure

```bash
docker compose up -d
```

The demo does not wait on these containers. The API logs a warning and continues when NATS or Temporal refuse the connection. TypeDB loaders (`python -m loaders.run_all` from `Backend`) are for the legacy department graph, not for the founder rehearsal.

## Model Backend Setup

Persona generation and round decisions share one selection rule, implemented in `Simulation/org_persona_generator.py` and `Simulation/orgsim_engine/decision_cascade.py`:

| Mode | How it is selected | What you set |
| --- | --- | --- |
| OpenAI | `OPENAI_API_KEY` starts with `sk-`, or `ORGSIM_USE_CLOUD_OPENAI=1` | `Simulation/.env` with `OPENAI_API_KEY` and `LLM_MODEL_NAME` set to an OpenAI model id, for example `gpt-4o-mini` |
| Ollama | Cloud mode is off | `OLLAMA_HOST` (default `http://127.0.0.1:11434`). `LLM_MODEL_NAME` defaults to `qwen2.5:14b`, which is also the compose default |
| Rules | The chosen endpoint errors or is absent | Nothing. The run continues with template-based persona text and round actions |

`Simulation/.env` is gitignored. A Tavily key in that file is read by the persona generator for optional enrichment; the rehearsal still runs without it.

Example cloud env file:

```bash
# Simulation/.env
OPENAI_API_KEY=sk-...
LLM_MODEL_NAME=gpt-4o-mini
ORGSIM_USE_CLOUD_OPENAI=1
```

Example local model:

```bash
# Simulation/.env
OLLAMA_HOST=http://127.0.0.1:11434
LLM_MODEL_NAME=qwen2.5:14b
```

## Running CivicBridge

Start the three processes from [Rehearsal Loop](#rehearsal-loop). Health checks:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/health
```

UI routes, with `en` unprefixed:

| Route | Page |
| --- | --- |
| `http://localhost:3000/simulate` | Intake, live trace, risk map |
| `http://localhost:3000/dashboard` | Planning-domain overview |
| `http://localhost:3000/report/<run_id>` | Action report |
| `http://localhost:3000/es/simulate` | Same screen in Spanish. Also `fr`, `it`, `zh`, `ja`, `ru` |

Tests:

```bash
pytest Simulation/tests -v
pytest Backend/tests/test_stub_snapshot.py -v
cd Frontend && npm run lint && npm run build
```

`Backend/demo/seed_demo.py` still drives the old department scenario against port 8000 (`python -m demo.seed_demo`, optional `--start-api`, `--skip-loaders`). Use the rehearsal screen or the `track` curl above for CivicBridge.

## API Fields

`POST /simulate` accepts this body (`Backend/api/routes/simulate.py`). Status code is 202. Poll `GET /simulate/{run_id}` or listen on `/ws/simulation/{run_id}`.

| Field | Description |
| --- | --- |
| `decision` | Situation text. Required, non-empty. The UI prepends key facts and uncertainty chips. |
| `track` | `founder` or `first1000`. When set, department names are ignored and advisor templates come from `infra/config.yaml`. |
| `departments` | Legacy only. Required when `track` is omitted. Allowed names: Sales, Finance, Operations, HR, Engineering, Marketing. |
| `engine` | `cascade` or `swarm`. Default `swarm`. |
| `rounds` | Integer 1–40. The UI sends 4 for swarm and 15 for cascade. The streaming pipeline caps swarm at 15 rounds. |
| `swarm_size` | Pool size for swarm. Default 24. Bounds 4–512. |
| `max_active_per_round` | Speakers per swarm round. Default 8. Bounds 2–128. |

`GET /simulate/{run_id}` adds `messages`, `conflicts`, `report`, and `recommendation` once the snapshot is attached. Report keys include `executive_summary`, `key_risks`, `recommended_actions`, `known_facts`, `unknown_facts`, `must_verify_facts`, `professional_questions`, `source_links`, `caveat`, and `confidence_score`. `confidence_score` is a rehearsal score, not an approval probability.

Simulation service routes on port 8001:

| Route | Role |
| --- | --- |
| `GET /health` | Liveness. The API uses this to decide live vs stub. |
| `POST /generate-personas` | Build personas for a decision and optional `track`. |
| `POST /stream-simulation` | NDJSON event stream for one run. |
| `POST /run-simulation` | Blocking run. |
| `POST /extract-conflicts` | Risk extraction over a message list. |
| `POST /generate-report` | Report compilation. |

## Customizing Advisor Behavior

Track membership is `simulation.advisor_tracks` in `infra/config.yaml`. Point `ORGSIM_CONFIG` at another YAML file to override the path. The loader merges that file over the defaults in `Simulation/config_loader.py`.

Edit a persona by changing its YAML file under `Simulation/templates/` and restarting the Simulation service. Fields that steer behavior:

- `role_title`, `department`, `agent_id` — what the transcript and risk map show
- `data_scope` / `action_scope` — including `forbidden` actions such as `guarantee_outcome`
- `behavioral_bias` — `primary_kpi`, `risk_tolerance`, pushback and alignment triggers

UI copy, the prefilled founder situation, uncertainty chips, and the safety note are in `Frontend/messages/en.json` under `simulate` (and the matching locale files). Restart `npm run dev` after editing them.

The rehearsal screen's track is the constant `DEFAULT_TRACK` in `Frontend/app/[locale]/simulate/page.tsx`. It is `founder`.

## Advanced Configuration

| Variable | Where | Effect |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `Frontend/.env.local` | API origin. Default `http://localhost:8000`. Restart Next after changing it. |
| `SIMULATION_SERVICE_URL` | API process | Explicit Simulation base URL. When unset, the API probes `http://127.0.0.1:8001`. |
| `ORGSIM_CONFIG` | Simulation process | Config YAML path. Default `infra/config.yaml`. |
| `ORGSIM_ALLOW_MOCK_WEBSOCKET` | API process | `1` / `true` / `yes` enables the scripted advisor stream when no live queue is attached. Off by default. |
| `OPENAI_API_KEY`, `ORGSIM_USE_CLOUD_OPENAI`, `LLM_MODEL_NAME`, `OLLAMA_HOST` | Simulation process | Model selection. See [Model Backend Setup](#model-backend-setup). |
| `TYPEDB_HOST`, `TYPEDB_PORT` | API process | Health check. Defaults `localhost:1729`. |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | API process | Health check. Compose sets the local Neo4j auth. |
| `NATS_URL` | API and Simulation | Default `nats://localhost:4222`. Publish is skipped when NATS is down. |

Swarm defaults in `infra/config.yaml`: engine `swarm`, `swarm_size` 24, `max_active_per_round` 8, `swarm_peer_recent` 10, `swarm_context_messages` 120.

Runs are stored in process memory (`Backend/api/run_store.py`). Restarting the API drops them. There is no checkpoint directory in v1.

## Troubleshooting

**`Failed to start simulation` in the browser.** The UI cannot reach the API. Confirm `curl http://127.0.0.1:8000/health` and that `NEXT_PUBLIC_API_URL` matches that origin. Restart `npm run dev` after changing `.env.local`.

**Risk map stays empty and the socket reports no live stream.** The Simulation service was not up when the run was created, or the WebSocket connected after the queue closed. Start port 8001, then start a new run. `GET /simulate/{id}` can still return a stub report.

**Persona logs say the seed report is missing.** Expected for CivicBridge templates until `Backend/output/*_seed.md` exists. The generator uses a stub seed and continues.

**Ollama model 404, or `DSPy/Ollama unavailable`.** The process is pointed at a local model that is not loaded. Pull that model, point `LLM_MODEL_NAME` at one that exists, or unset the cloud key and let the rule fallback run. The fallback is the supported demo path.

**`uvicorn` or `pytest` immediately exits 126.** The virtualenv scripts were created in another directory and their shebangs are stale. Recreate `.venv` in this clone (`python3.11 -m venv .venv`) or invoke `python -m uvicorn` and `python -m pytest` with that interpreter.

**Port already in use.** API default is 8000, Simulation 8001, Next 3000. Pass `--port` to uvicorn or `npm run dev -- --port 3001`. If Next moves, CORS on the API already allows localhost on any port; set `NEXT_PUBLIC_API_URL` if the API is not on 8000.

**Report language promises an outcome.** That is a bug. Persona templates forbid outcome guarantees, and the report caveat is supposed to stay a planning aid. File it against the template or `Simulation/report_agent.py` rather than treating the sentence as guidance.

## Results

Shipped v1.0 was audited on 2026-05-09. A local founder cascade was run on 2026-10-26 with the on-screen demo and the rule-based fallback.

| Check | Result |
| --- | --- |
| v1 requirements | 23 / 23 satisfied |
| Phases verified | 6 / 6 |
| Critical paths | Intake → live simulation → report; backend stub → report; WebSocket history → report |
| Example founder cascade | Completed. 60 advisor messages across 15 rounds. Report hydrated on GET |
| Report contents | Known facts, open uncertainties, verify-before-acting items, professional questions, source links, caveat |
| Simulation tests | 16 passed |
| Stub report test | 1 passed (`Backend/tests/test_stub_snapshot.py`) |
| Languages in the UI | English, Spanish, French, Italian, Chinese, Japanese, Russian |

| Track | Advisors | What the rehearsal is for |
| --- | --- | --- |
| `founder` | Immigration Attorney, Evidence Coach, Founder Mentor, Tax / Company Navigator | Compare a pathway, evidence, company setup, and timing. The output is a rehearsal, not an eligibility decision. |
| `first1000` | Banking, Healthcare, Housing, Tax, Local Systems | Sequence identifiers, money, coverage, housing, and taxes, and list what still needs a professional or an official page. |

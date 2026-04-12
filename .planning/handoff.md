# Session Handoff — OpenAI + Tavily Integration

## Task
Wire up OpenAI GPT-4o-mini and Tavily API into the OrgSim simulation engine,
replacing Ollama as the LLM backend.

## API Keys (store in Simulation/.env ONLY — never in source)
OPENAI_API_KEY=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
TAVILY_API_KEY=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
LLM_MODEL_NAME=gpt-4o-mini

## Files to change

### 1. Simulation/.env (create/overwrite)
```
OPENAI_API_KEY=<key above>
TAVILY_API_KEY=<key above>
LLM_MODEL_NAME=gpt-4o-mini
```

### 2. .gitignore — ensure .env is listed (currently only .venv/ is there)
Add: `**/.env`

### 3. requirements.txt — add dependencies
```
tavily-python>=0.3.0
openai>=1.0.0
```

### 4. Simulation/org_persona_generator.py
- Replace `_configure_dspy_ollama()` with OpenAI config:
  ```python
  dspy.LM(model="openai/gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7, max_tokens=512)
  ```
- Add `_tavily_enrich(decision, dept)` before persona build:
  fetches market context (CAC, benchmarks, industry data) and appends to seed_report
  Query pattern: f"{dept} department {decision} business impact benchmarks 2024"

### 5. Simulation/conflict/extractor.py
- Replace `_configure_dspy()` with same OpenAI config (temp=0.3, max_tokens=256)

### 6. Simulation/report_agent.py
- Replace `_configure_dspy()` with OpenAI config (temp=0.4, max_tokens=1024)
- Add `_tavily_precedents(decision)` called before report compilation:
  searches for real case studies matching the decision pattern
  appends as "Historical Precedent" section in the executive report

## Current state
- Backend running on port 8000 (mock stream working, 4s NATS fallback)
- Simulation service (port 8001) NOT running — needs to be started after changes
- Frontend split-layout working (left: scenario/feed/conflicts, right: D3 network)
- NATS running, Temporal not running (stub mode)
- TypeDB running but DB unpopulated (cascade tracer uses static fallback)

## Primary demo scenario
"CFO cuts Q4 marketing budget by 20%" — 4 agents: CFO, VP Sales, Ops Lead, HR Director

## Architecture note
DSPy uses "openai/gpt-4o-mini" model string format (provider prefix required).
Tavily Python client: `from tavily import TavilyClient`
Both keys loaded via `python-dotenv` from Simulation/.env

## Run order after changes
1. cd Backend && uvicorn api.main:app --port 8000
2. cd Simulation && uvicorn simulation.app:app --port 8001
3. Open http://localhost:3000/simulate

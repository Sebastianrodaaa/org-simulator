# tasks.md — OrgSim agent coordination

## Status key
[ ] todo | [~] in progress (add agent name) | [x] done | [!] blocked (add reason)

---

## Phase 0 — Foundation (target: 2-3 hrs)

[x] Create infra/mock/sales_pipeline.csv (25 deals: deal_id, deal_name, value_usd, stage, owner, product, department, close_date, probability_pct)
[x] Create infra/mock/finance_pl.json (Q1-Q4 P&L, budget lines per dept, runway_months=18, Q4 marketing=$280k)
[x] Create infra/mock/ops_capacity.yaml (engineering capacity_pct=94, devops capacity_pct=88, open incidents, infra cost)
[x] Create infra/mock/hr_people.json (headcount, attrition_rate, open_reqs, engagement_score, top_performer_flight_risk per dept)
[x] Fix docker-compose.yml: upgraded TypeDB 2.28→3.3.0, removed GPU block for Mac Ollama, fixed healthchecks
[!] Pull Ollama model: `docker compose exec ollama ollama pull qwen2.5:14b` (from repo root; or `docker exec orgsim-ollama ollama pull qwen2.5:14b` as one line) [BLOCKED: Docker Desktop not running — start it first]

## Phase 1 — Data ingestion + TypeDB ontology (target: 3-4 hrs)

[x] Write backend/schema/orgsim.tql (TypeDB 3.x syntax: Department, Employee, Product, Deal, BudgetLine, Metric + Ownership/CrossDeptDependency/Employs relations)
[x] Write backend/schema/init_db.py (connect, create DB if missing, apply schema)
[x] Write backend/loaders/sales_loader.py (CSV → TypeDB, 4-pass: dept→employees→products→deals+ownership)
[x] Write backend/loaders/finance_loader.py (JSON → TypeDB; also creates Marketing dept entity)
[x] Write backend/loaders/ops_loader.py (YAML → TypeDB; creates Engineering + Operations dept entities)
[x] Write backend/loaders/hr_loader.py (JSON → TypeDB; creates HR dept entity)
[x] Write backend/loaders/entity_resolver.py (creates 3 CrossDeptDependency relations)
[x] Write backend/loaders/run_all.py (orchestrates all 7 steps including seed report generation)
[x] Write backend/seed_reports/generator.py (TypeQL queries → markdown reports per dept)
[x] Write backend/tests/test_schema.py (integration tests — requires TypeDB running + loaders executed)
[!] Output: backend/output/*_seed.md [BLOCKED: needs Docker running — run: cd backend && python -m loaders.run_all]

## Phase 2 — MiroFish fork adaptation (target: 4-5 hrs)

[x] Clone nikmcfly/MiroFish-Offline into simulation/mirofish/
[x] Write simulation/templates/cfo.yaml (CFO persona: cost-control bias, pushes back on spend)
[x] Write simulation/templates/vp_sales.yaml (pipeline bias, resists delays)
[x] Write simulation/templates/ops_lead.yaml (capacity bias, flags overcommitment)
[x] Write simulation/templates/hr_director.yaml (retention bias, flags morale risk)
[x] Adapt simulation/mirofish/persona_generator.py to load org templates instead of public personas
[x] Replace Twitter/Reddit platform model with internal discussion thread (decision_cascade channel)
[x] Large-swarm engine: `orgsim_engine/swarm_cascade.py` + `swarm/persona_pool.py` + `infra/config.yaml` (`engine: swarm`, `POST /run-simulation` fields)
[x] Remap social graph fields: followers→reports_to, influence_score→budget_authority
[x] Integration test: feed sales_seed.md → verify 4 agent personas are generated with correct biases

## Phase 3 — Simulation engine + conflict detection (target: 4-5 hrs)

[x] Write backend/api/main.py (FastAPI app, CORS, routers registered)
[x] Write backend/api/routes/health.py (GET /health — real socket checks for TypeDB/Neo4j/NATS)
[x] Write backend/api/routes/simulate.py (POST /simulate, GET /simulate/{run_id} — stub with background task)
[x] Write backend/api/ws/simulation.py (WS /ws/simulation/{run_id} — 15 mock agent messages then complete)
[x] Verify API: both /health and POST /simulate return valid JSON (tested with uvicorn + curl)
[x] Write backend/api/nats_client.py (JetStream, ORGSIM stream, allow_reconnect=False, nats logger suppressed)
[x] Write backend/api/temporal/client.py + temporal/workflow.py (OrgSimWorkflow + 4 activity stubs, retry policies)
[x] Update backend/api/routes/simulate.py (Temporal trigger + status query, graceful stub fallback)
[x] Update backend/api/ws/simulation.py (NATS relay with conflict events, mock fallback)
[x] Update backend/api/main.py (lifespan: NATS + Temporal connect/disconnect)
[x] Write backend/tests/test_e2e.py (7 tests: health, CRUD, validation, stub progression, WebSocket, demo scenario)
[x] Verified: clean startup, /health→200 degraded, POST /simulate→202 pending, GET→complete after 10s
[x] Write simulation/app.py (FastAPI HTTP service port 8001) [Simulation agent]
[x] Write simulation/conflict/extractor.py (parse agent logs → structured conflict objects) [Simulation agent]
[x] Write simulation/cascade/tracer.py (TypeDB traversal → downstream dept impact map) [Simulation agent]
[x] Write simulation/report_agent.py (DSPy-compiled report builder from sim output) [Simulation agent]
[ ] Write simulation/orgsim_workflow.py (Temporal workflow wrapping MiroFish run)
[ ] NATS publisher: emit events per agent message, conflict detection, and run completion
[ ] End-to-end test: "CFO cuts Q4 marketing budget 20%" → conflicts surface within 60s

## Phase 4 — Frontend dashboard (target: 3-4 hrs)

[x] Scaffold Next.js 15 app in frontend/ (TypeScript, Tailwind, App Router) [Frontend agent]
[x] Build frontend/app/dashboard/page.tsx (dept health overview, entity cards) [Frontend agent]
[x] Build frontend/app/simulate/page.tsx (scenario input, live agent feed, conflict panel) [Frontend agent]
[x] Build frontend/app/report/[id]/page.tsx (prediction report viewer) [Frontend agent]
[x] D3 force graph: cross-dept conflict visualization [Frontend agent]
[x] Add swarm interaction visualizer (agent-level nodes + inferred interaction edges) to `frontend/app/simulate/page.tsx` [Frontend agent]
[x] WebSocket client hook: useSimulationStream(runId) [Frontend agent]
[x] API client: frontend/lib/api.ts [Frontend agent]

## Phase 5 — Demo hardening (target: 2-3 hrs)

[x] Pre-seed demo scenario: backend/demo/seed_demo.py (polls to complete, prints run_id + conflicts + report URL)
[x] Add loading skeletons, empty states, mobile layout fixes, demo URL pre-fill (?demo=true) [Frontend agent]
[x] Demo timing: 15-round default set in simulation/app.py (fallback=22ms; Ollama bottleneck is persona gen ~60s, not rounds)
[x] Persona quality: CFO proposes cut citing runway, VP Sales flags $4.25M pipeline risk, Ops flags 94% capacity, HR flags 7.2 engagement/12% attrition
[ ] 60-second verbal pitch written and rehearsed
[ ] Backup screen recording of full demo flow
[x] README.md: 8-min quick-start verified, key files map, test commands

---

## Notes / blockers
- TypeDB driver: use typedb-driver==3.x (pip install typedb-driver), NOT typedb-client 2.x
- Ollama: qwen2.5:14b is faster for demo, qwen2.5:32b is more accurate — start with 14b
- MiroFish default LLM_BASE_URL points to DashScope — must be overridden to Ollama in .env
- Temporal requires Java 11+ on host for the server, OR use the Docker image (recommended)
- docker-compose.yml updated: TypeDB image → typedb/typedb:3.3.0; GPU deploy block removed (Mac)
- Marketing dept entity created in finance_loader.py (needed for CrossDeptDependency resolver)
- All TypeDB 3.x insert queries wrapped in list(tx.query(...)) to consume iterator
- To run loaders after Docker up: cd backend && python -m loaders.run_all
- To run tests after loaders: pytest tests/test_schema.py -v

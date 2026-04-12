# tasks.md — OrgSim agent coordination

## Status key
[ ] todo | [~] in progress (add agent name) | [x] done | [!] blocked (add reason)

---

## Phase 0 — Foundation (target: 2-3 hrs)

[ ] Create infra/mock/sales_pipeline.csv (20 deals, fields: deal_id, name, value, stage, owner, product, close_date)
[ ] Create infra/mock/finance_pl.json (Q1-Q4 P&L, budget lines per dept, runway_months)
[ ] Create infra/mock/ops_capacity.yaml (team capacity %, open incidents, infra cost, headcount)
[ ] Create infra/mock/hr_people.json (headcount, attrition_rate, open_reqs, engagement_score per dept)
[ ] Verify docker-compose.yml: all 5 services start cleanly (TypeDB, Neo4j, NATS, Temporal, Ollama)
[ ] Pull Ollama model: docker exec orgsim-ollama ollama pull qwen2.5:14b

## Phase 1 — Data ingestion + TypeDB ontology (target: 3-4 hrs)

[ ] Write backend/schema/orgsim.tql (Department, Employee, Product, Budget, Metric, Relationship types)
[ ] Write backend/loaders/sales_loader.py (CSV → TypeDB)
[ ] Write backend/loaders/finance_loader.py (JSON → TypeDB)
[ ] Write backend/loaders/ops_loader.py (YAML → TypeDB)
[ ] Write backend/loaders/hr_loader.py (JSON → TypeDB)
[ ] Write backend/loaders/entity_resolver.py (cross-dept entity dedup and linking)
[ ] Write backend/seed_reports/generator.py (TypeQL queries → markdown reports per dept)
[ ] Write backend/tests/test_schema.py (verify cross-dept queries return expected results)
[ ] Output: backend/output/sales_seed.md, finance_seed.md, ops_seed.md, hr_seed.md

## Phase 2 — MiroFish fork adaptation (target: 4-5 hrs)

[ ] Clone nikmcfly/MiroFish-Offline into simulation/mirofish/
[ ] Write simulation/templates/cfo.yaml (CFO persona: cost-control bias, pushes back on spend)
[ ] Write simulation/templates/vp_sales.yaml (pipeline bias, resists delays)
[ ] Write simulation/templates/ops_lead.yaml (capacity bias, flags overcommitment)
[ ] Write simulation/templates/hr_director.yaml (retention bias, flags morale risk)
[ ] Adapt simulation/mirofish/persona_generator.py to load org templates instead of public personas
[ ] Replace Twitter/Reddit platform model with internal discussion thread (decision_cascade channel)
[ ] Remap social graph fields: followers→reports_to, influence_score→budget_authority
[ ] Integration test: feed sales_seed.md → verify 4 agent personas are generated with correct biases

## Phase 3 — Simulation engine + conflict detection (target: 4-5 hrs)

[ ] Write backend/api/routes/simulate.py (POST /simulate, GET /simulate/{run_id})
[ ] Write backend/api/ws/simulation.py (WebSocket /ws/simulation/{run_id})
[ ] Write simulation/orgsim_workflow.py (Temporal workflow wrapping MiroFish run)
[ ] Write simulation/conflict/extractor.py (parse agent logs → structured conflict objects)
[ ] Write simulation/cascade/tracer.py (TypeDB traversal → downstream dept impact map)
[ ] Write simulation/report_agent.py (DSPy-compiled report builder from sim output)
[ ] NATS publisher: emit events per agent message, conflict detection, and run completion
[ ] End-to-end test: "CFO cuts Q4 marketing budget 20%" → conflicts surface within 60s

## Phase 4 — Frontend dashboard (target: 3-4 hrs)

[ ] Scaffold Next.js 15 app in frontend/ (TypeScript, Tailwind, App Router)
[ ] Build frontend/app/dashboard/page.tsx (dept health overview, entity cards)
[ ] Build frontend/app/simulate/page.tsx (scenario input, live agent feed, conflict panel)
[ ] Build frontend/app/report/[id]/page.tsx (prediction report viewer)
[ ] D3 force graph: cross-dept conflict visualization
[ ] WebSocket client hook: useSimulationStream(runId)
[ ] API client: frontend/lib/api.ts

## Phase 5 — Demo hardening (target: 2-3 hrs)

[ ] Pre-seed demo scenario: "CFO cuts Q4 marketing budget 20%"
[ ] Add loading skeletons to all async UI sections
[ ] 60-second verbal pitch written and rehearsed
[ ] Backup screen recording of full demo flow
[ ] README.md: architecture diagram, setup steps, novelty statement

---

## Notes / blockers
- TypeDB driver: use typedb-driver==3.x (pip install typedb-driver), NOT typedb-client 2.x
- Ollama: qwen2.5:14b is faster for demo, qwen2.5:32b is more accurate — start with 14b
- MiroFish default LLM_BASE_URL points to DashScope — must be overridden to Ollama in .env
- Temporal requires Java 11+ on host for the server, OR use the Docker image (recommended)

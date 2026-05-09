# Codebase Concerns

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## High-Impact Concerns

### Domain Coupling

The app is deeply coupled to organization simulation language:

- `VALID_DEPARTMENTS` in `Backend/api/routes/simulate.py`.
- `ALL_DEPTS`, `DEPT_COLOR`, and `DEMO_DECISION` in `Frontend/app/simulate/page.tsx`.
- `DeptName` and conflict department fields in `Frontend/lib/types.ts`.
- YAML templates under `Simulation/templates/`.
- TypeDB schema and loaders under `Backend/schema/` and `Backend/loaders/`.

This is the main work area for the hackathon repurpose.

### Report Route Data Mismatch

`Frontend/app/report/[id]/page.tsx` expects optional `messages`, `conflicts`, and `report` on the result from `getSimulation()`. `Backend/api/routes/simulate.py` currently returns `SimulationRun`, which includes run metadata and recommendation but not full transcript, conflicts, or report data.

For a polished immigration tool, the report route should either:

- Persist and return events/transcript/conflicts/report data, or
- Generate a report client-side from event history before navigation, or
- Add an API endpoint specifically for run details.

### Legal/Advice Safety

The current product has no legal guidance boundary because it is a business simulation demo. The immigration repurpose must avoid implying legal advice. It needs careful copy and output structure:

- "Planning aid, not legal advice."
- Clear uncertainty and source fields.
- Escalation prompts for lawyer review.
- No guarantee language for visa eligibility or immigration outcomes.

### Source Freshness

Immigration rules, fees, forms, and timelines change. The current app can use Tavily, but no official-source citation pipeline exists. Hackathon scope should either avoid making live legal claims or add a constrained source retrieval layer against official sources.

### Heavy Infrastructure

The root demo stack includes TypeDB, Neo4j, NATS, Temporal, Ollama, API, simulation service, and frontend. This is powerful but heavy for judging/demo setup.

The shortest reliable demo path is:

- Frontend.
- Backend API.
- Simulation service.
- Rule-based or local LLM fallback.

TypeDB/Neo4j/NATS/Temporal should be optional unless a phase explicitly requires them.

## Security And Configuration Concerns

- Development credentials/defaults exist in config and helper files.
- CORS is fixed to `http://localhost:3000`.
- OpenAI and Tavily keys are read from environment variables; generated docs should not expose actual `.env` contents.
- The repo contains generated/cache directories such as `Frontend/.next`, `Frontend/node_modules`, and Python `__pycache__` files.

## Performance Concerns

- Swarm mode runs LLM calls in a `ThreadPoolExecutor`; timeout defaults are long (`ORGSIM_SWARM_ROUND_TIMEOUT`, `ORGSIM_CASCADE_ROUND_TIMEOUT`).
- Streaming intentionally delays messages with `asyncio.sleep()` for UI pacing, which improves demo feel but affects total runtime.
- Large `swarm_size` values can produce expensive or slow runs if actual LLM calls are enabled.
- Rule-based fallback is fast and should remain available for demos.

## Maintainability Concerns

- `Simulation/app.py` is large and mixes API models, route handlers, NATS publishing, engine orchestration, conflict extraction, and report generation.
- `Simulation/org_persona_generator.py` imports private helpers from itself in `Simulation/swarm/persona_pool.py`.
- Some current comments/docs reference lowercase `backend`/`frontend` paths, while actual folders are capitalized.
- `Simulation/mirofish/` is a large embedded project; accidental edits there could burn time.

## Repurpose Risks

- A shallow rename would leave business-specific fallback text, metrics, and conflict heuristics in outputs.
- Reusing "conflict" language directly may make the immigration tool feel adversarial; "risk", "blocker", "tradeoff", or "dependency" may fit better.
- Immigration users need actionability and trust more than spectacle. The simulation should end in next steps, documents/evidence, deadlines, and who to ask for help.
- "Learning to be American" features should avoid stereotyping and should focus on systems navigation: banking, credit, healthcare, housing, taxes, work, school, transportation, and local norms.

## Suggested Immediate Mitigations

- Create an immigration-domain configuration layer before editing the engine deeply.
- Keep old OrgSim behavior only as reference or remove it from the visible UI.
- Build one end-to-end scenario first: founder visa strategy or first-1000-days onboarding.
- Add a lightweight report persistence path before investing in report UI polish.
- Keep fallback deterministic so judges can see the product without external credentials.


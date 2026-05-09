# Codebase Testing

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## Test Frameworks

- Python tests use `pytest`.
- Async-related dependencies include `pytest-asyncio`.
- Frontend linting is available through `npm run lint` in `Frontend/package.json`.
- No dedicated frontend test runner is currently declared in `Frontend/package.json`.

## Python Test Locations

- `Backend/tests/test_schema.py` checks TypeDB schema/data loading and seed report generation.
- `Backend/tests/test_e2e.py` checks API health, simulation creation, polling, validation, WebSocket events, and demo completion.
- `Simulation/tests/test_swarm.py` checks swarm persona counts, active-agent caps, and cascade window behavior.
- `Simulation/tests/test_persona_gen.py` exists and should be reviewed when persona templates are replaced.

## Test Execution

From repository docs:

- Schema/unit-ish test: `cd Backend && pytest tests/test_schema.py -v`.
- End-to-end test: `pytest tests/test_e2e.py -v -m e2e`.
- Simulation tests can be run from root or `Simulation/` with `pytest Simulation/tests -v`.

The schema and e2e tests require infrastructure or reachable services. Many tests skip when services are unavailable.

## Current Test Assumptions

- The demo scenario is a CFO marketing-budget cut.
- Departments include Sales, Finance, Engineering, HR, and Marketing.
- TypeDB contains organization-specific entities and dependencies.
- Seed reports exist under `Backend/output/`.
- WebSocket tests expect at least one `agent_message` and a `complete` event.
- Demo acceptance currently expects at least one conflict for the CFO budget scenario.

## Useful Existing Coverage

- API validation of empty decision and invalid department in `Backend/tests/test_e2e.py`.
- API run creation and lookup in `Backend/tests/test_e2e.py`.
- WebSocket stream shape in `Backend/tests/test_e2e.py`.
- Swarm size and per-round active cap in `Simulation/tests/test_swarm.py`.
- TypeDB dependency and seed report checks in `Backend/tests/test_schema.py`.

## Testing Gaps

- No frontend component/page tests are present.
- No tests assert `Frontend/lib/wireSimulationEvents.ts` mapping behavior.
- `GET /simulate/{run_id}` returns basic run data, while `Frontend/app/report/[id]/page.tsx` expects optional messages, conflicts, and report fields; this mismatch needs test coverage.
- No tests cover immigration-specific safety disclaimers, legal-source handling, or "not legal advice" boundaries.
- No tests cover accessibility or mobile layout for the simulation screen.
- No tests verify that simulation fallback outputs are useful when LLM services are unavailable for non-demo scenarios.

## Repurpose Test Plan

For the immigration hackathon version, add or update tests around:

- New valid track/advisor labels replacing `VALID_DEPARTMENTS`.
- Scenario intake validation for Founder Immigration and Learning to be American.
- Persona generation from immigration/system-navigation templates.
- Risk extraction categories such as eligibility, evidence, timing, cost, compliance, housing, healthcare, credit, and tax.
- Streaming contract stability for `agent_message`, `risk`, `complete`, and report events.
- Report output including action items, caveats, confidence/uncertainty, and source/citation placeholders.
- Demo scenarios that complete quickly without requiring cloud APIs.

## Commands To Run After Repurpose

- `pytest Simulation/tests -v`
- `pytest Backend/tests/test_e2e.py -v -m e2e` with API and simulation services running
- `cd Frontend && npm run lint`
- `cd Frontend && npm run build`


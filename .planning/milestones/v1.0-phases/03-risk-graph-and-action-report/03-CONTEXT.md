# Phase 3 — Risk graph & action report

**Status:** Complete (execution)  
**Date:** 2026-05-09

## Scope

- Risk-oriented copy and FE types (`risk_category`, extended `ReportDict`).
- Dynamic advisor-lane graph (`ConflictGraph`) driven by streamed departments.
- Mock WebSocket script aligned with CivicBridge advisor lanes.
- Report route: risk timeline, optional structured sections (facts, verify, professionals, sources, caveat).
- Backend snapshot enrichment for GET run payloads (see `Backend/api/simulation_snapshot.py`).
- Conflict extractor repair + unit tests for risk metadata.

## Verification

- `pytest Simulation/tests` — pass (includes `test_extractor_risk_metadata`).
- `npm run lint` / `npm run build` (Frontend) — pass.

See `03-VERIFICATION.md` for checklist.

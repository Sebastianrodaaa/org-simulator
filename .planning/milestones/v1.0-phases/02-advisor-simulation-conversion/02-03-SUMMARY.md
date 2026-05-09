---
phase: 02-advisor-simulation-conversion
plan: 02-03
subsystem: api-frontend
tags: [fastapi, nextjs, track]
requirements-completed: [SIM-01, SIM-02, SIM-03, SIM-04, SAFE-02]
completed: 2026-05-09
---

# Phase 2 Plan 02-03 Summary

**Track flows from UI → Backend → Simulation `generate-personas`.**

- `SimulateRequest`: optional `track`; `model_validator` skips legacy `VALID_DEPARTMENTS` when `track` is set; empty `departments` allowed for CivicBridge.
- `run_live_streaming_pipeline` sends `track` in POST body when present.
- `startSimulation` options include `track`; `/simulate` page passes `track` and `[]` departments.
- Removed `COMPATIBILITY_DEPTS` shim; stub recommendation text is CivicBridge-neutral.

**Checks:** `npm run lint` and `npm run build` succeeded.

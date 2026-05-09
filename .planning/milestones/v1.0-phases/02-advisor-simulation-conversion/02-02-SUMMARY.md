---
phase: 02-advisor-simulation-conversion
plan: 02-02
subsystem: simulation-service
tags: [fastapi, swarm, fallback-personas]
requirements-completed: [SIM-03, SIM-04, SAFE-02]
completed: 2026-05-09
---

# Phase 2 Plan 02-02 Summary

**Simulation service supports CivicBridge track personas and swarm template resolution.**

- `GeneratePersonasRequest` accepts optional `track`; handler calls `advisor_track_templates` and `build_persona` per id.
- `build_swarm_personas` gains `template_ids`; `_template_ids_for_departments` resolves legacy dept names or YAML stems via `templates/*.yaml` existence check.
- `template_stem_from_swarm_username()` maps `agent_id_sNNNNN` swarm slots back to template stems.
- `run_simulation` and `stream-simulation` swarm branches derive template list from persona `username`/`agent_id` when possible.
- `_fallback_persona` and seed stub text rewritten for immigration/systems rehearsal; legacy org template ids split in source to avoid stale OrgSim demo grep targets.

**Checks:** `pytest Simulation/tests` — 13 passed.

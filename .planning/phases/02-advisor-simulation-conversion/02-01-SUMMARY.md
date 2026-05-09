---
phase: 02-advisor-simulation-conversion
plan: 02-01
subsystem: simulation-config
tags: [yaml, advisor-tracks, civicbridge]
requirements-completed: [SIM-01, SIM-02]
completed: 2026-05-09
---

# Phase 2 Plan 02-01 Summary

**Advisor YAML templates and `advisor_tracks` config are in place.**

- Added `simulation.advisor_tracks` to `infra/config.yaml` for `founder` and `first1000`.
- Implemented `advisor_track_templates()` in `Simulation/config_loader.py` with defaults merge.
- Created nine templates under `Simulation/templates/` with unique `department` strings per advisor (avoids swarm collapse on dedupe).

**Checks:** `advisor_track_templates` lengths 4/5; `_load_template` smoke for sample stems.

# Retrospective

Cross-milestone notes for CivicBridge / OrgSim planning.

## Milestone: v1.0 — CivicBridge hackathon v1

**Shipped:** 2026-05-09  
**Phases:** 6 | **Plans:** 10

### What shipped

Two-track CivicBridge simulator (Founder + First 1000 Days), persona/simulation stack conversion, risk and report UX, snapshot wiring so reports work on stub and WS fallbacks, tests and swarm visualization polish.

### What worked

- Reusing OrgSim’s queue/WebSocket/streaming spine while swapping domain content.
- Gap-closure phases (5–6) after audit kept a single-backend demo credible.
- Small, automated regression (`test_stub_snapshot`) for the highest-risk integration path.

### What was inefficient

- Frontend as submodule doubles release steps (two repos to push).
- Phase verification files varied in strictness (REQ-ID tables vs prose); milestone audit had to interpret.

### Patterns

- `attach_snapshot_to_run` as the single choke point for GET-shaped payloads.
- CivicBridge copy and templates co-evolved (UI, Simulation YAML, mock WS).

### Lessons

- Close stub/report gaps before calling a milestone “demo-safe.”
- Align e2e strings with product narrative early to avoid CFO-era drift.

---

## Cross-milestone trends

| Theme | v1.0 |
|-------|------|
| Planning discipline | GSD phases + audit + gap closure |
| Test pyramid | Simulation unit + backend stub regression + optional e2e |

---
*Started: 2026-05-09*

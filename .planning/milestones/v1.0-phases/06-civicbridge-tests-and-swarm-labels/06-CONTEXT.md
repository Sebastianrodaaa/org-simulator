# Phase 6: CivicBridge Tests and Swarm Labels - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning
**Mode:** Auto-generated (gap closure — autonomous)

<domain>
## Phase Boundary

Align e2e fixtures and copy with CivicBridge tracks; extend swarm graph colors for immigration advisor lane strings; keep SAFE-03 coverage meaningful.

</domain>

<decisions>
## Implementation Decisions

### Tests
- Replace `CFO` / Q4 demo strings with founder + first-1000-days rehearsal copy; use `track` + empty `departments` where applicable.
- Assert stub GET returns `report` in `test_stub_run_progresses_to_complete`.

### Swarm UI
- Add explicit `DEPT_COLORS` entries for mock lane labels; `fillForDept()` for keyword + hash fallback so unknown lanes are not all grey.

</decisions>

<code_context>
## Existing Code Insights

- `SwarmInteractionGraph.tsx` used only legacy Sales/Finance/Operations/HR colors.
- `test_e2e.py` still referenced business CFO scenario.

</code_context>

<specifics>
See milestone audit SAFE-03 / RISK-03 notes.

</specifics>

<deferred>
## Deferred Ideas

Full Simulation persona string audit — optional follow-up if fixtures remain.

</deferred>

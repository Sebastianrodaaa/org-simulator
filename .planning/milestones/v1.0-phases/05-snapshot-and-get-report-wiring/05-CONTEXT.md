# Phase 5: Snapshot and GET Report Wiring - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure / gap closure — discuss skipped per autonomous run)

<domain>
## Phase Boundary

Ensure every simulation completion path (backend stub, live streaming failure, WebSocket mock, honest no-stream) leaves `GET /simulate/{id}` with `messages`, `conflicts`, and structured `report` compatible with the report UI.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
- Stub path: append a short CivicBridge-shaped `event_history` then call `attach_snapshot_to_run`.
- Streaming `except`: call `attach_snapshot_to_run` before marking failed when partial history exists.
- Mock WS: mirror outbound events into `event_history` and attach snapshot when mock completes; add `round` for wire message ordering.
- Honest no-stream: call `attach_snapshot_to_run` after the complete frame so GET still returns the deterministic template report.

</decisions>

<code_context>
## Existing Code Insights

- `attach_snapshot_to_run` in `simulation_snapshot.py` already builds report from `event_history`.
- `_stub_run` previously ended without snapshot attachment (audit gap).

</code_context>

<specifics>
## Specific Ideas

Per `v1.0-MILESTONE-AUDIT.md` integration gaps: stub → snapshot, WS fallbacks → GET hydration.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

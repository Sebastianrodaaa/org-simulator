# Codebase Conventions

**Mapped:** 2026-05-09
**Scope:** Existing `ORG - SIM` repository

## Python Style

- Python modules use `from __future__ import annotations` consistently.
- Runtime code generally uses type hints for function parameters and return values.
- Pydantic models define API request/response contracts in `Backend/api/routes/simulate.py` and `Simulation/app.py`.
- Module docstrings are common and often describe routes, data shapes, and usage.
- Logging is preferred over print in services and loaders.
- Graceful degradation is a recurring pattern: NATS, Temporal, TypeDB, DSPy, Ollama, and the simulation service often fall back rather than crash the app.

## Error Handling

- API routes catch unexpected exceptions and return `HTTPException(status_code=500, ...)`.
- Background simulation work in `Backend/api/routes/simulate.py` updates run status to `failed` and attempts to emit an error event.
- Simulation integrations use broad exception handling around optional dependencies.
- TypeDB cascade tracing falls back to a static dependency table in `Simulation/cascade/tracer.py`.
- LLM persona/action generation falls back to rule-based outputs in `Simulation/org_persona_generator.py` and `Simulation/orgsim_engine/decision_cascade.py`.

## API Contract Patterns

- Public simulation creation request: `decision`, `departments`, `engine`, `rounds`, `swarm_size`, `max_active_per_round`.
- Internal simulation service request: `run_id`, `personas`, `decision`, `rounds`, engine options.
- WebSocket event types: `agent_message`, `conflict`, `complete`, `error`.
- Frontend normalizes multiple event shapes in `Frontend/lib/wireSimulationEvents.ts`, which is a useful compatibility layer for repurposing.

## Frontend Style

- Next.js App Router pages are under `Frontend/app/`.
- Client components use `'use client'` at the top.
- Styling is Tailwind utility classes in JSX.
- UI uses compact operational screens rather than marketing pages.
- State is local React state for the main simulator; no global store is present.
- The simulation page is a split-pane tool surface: input/feed on the left, graph on the right.

## Data Shape Conventions

- Python simulation messages use `msg_id`, `round`, `agent_id`, `role`, `department`, `content`, `action`, `target_msg_id`, `timestamp`, `budget_authority`, and `reports_to_count`.
- Frontend `MessageDict` uses `message_id`, `run_id`, `round`, `agent_role`, `department`, `content`, `action_type`, and `timestamp`.
- Conflict records use `conflict_id`, `dept_a`, `dept_b`, `conflict_type`, `severity`, `description`, `round_detected`, `agent_a_message`, and `agent_b_message`.
- Repurposing should either preserve these shapes with relabeled fields for speed or introduce a migration layer that maps new immigration concepts into current UI expectations.

## Configuration Conventions

- `infra/config.yaml` is the central non-code configuration for simulation labels and tuning.
- `Simulation/config_loader.py` merges YAML values over defaults.
- Environment variables override infrastructure and LLM endpoints.
- YAML persona templates in `Simulation/templates/` define role behavior, KPIs, permitted actions, and triggers.

## Comments And Documentation

- Many source files have useful top-level docstrings.
- Comments are practical, especially around streaming, fallback behavior, and demo pacing.
- Some README instructions and comments use lowercase paths that do not match the actual `Backend` and `Frontend` directory capitalization.

## Repurpose Conventions To Preserve

- Keep the run lifecycle simple: create run, stream events, show complete report.
- Keep fallback behavior for demos.
- Keep persona templates as data files so hackathon iteration is fast.
- Keep `wireSimulationEvents.ts` as a boundary between backend changes and UI rendering.
- Keep scenario examples in one place instead of scattering immigration prompt text across the codebase.


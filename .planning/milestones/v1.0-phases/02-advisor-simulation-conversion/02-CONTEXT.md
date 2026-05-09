# Phase 2: Advisor Simulation Conversion - Context

**Gathered:** 2026-05-09 (auto mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the business department/persona system with immigration and systems-navigation advisor simulations. The simulation pipeline (FastAPI → Simulation service → WebSocket → frontend) stays intact; only the domain layer changes. Specifically: backend API validation accepts advisor tracks, YAML templates define immigration advisors, persona generation produces immigration-domain opinions, and visible fallback text references immigration context instead of CFO/Q4/Sales/HR. Risk extraction and the report UI belong to Phase 3.

</domain>

<decisions>
## Implementation Decisions

### API Compatibility Strategy

- **D-01:** Add an optional `track: Literal["founder", "first1000"] | None` field to `SimulateRequest` in `Backend/api/routes/simulate.py`.
- **D-02:** When `track` is provided, the backend auto-selects the advisor templates for that track; `departments` validation is relaxed (either made optional or expanded to accept advisor names). The frontend passes `track` instead of hardcoded `COMPATIBILITY_DEPTS`.
- **D-03:** The `VALID_DEPARTMENTS` set in the backend is replaced or supplemented so runs do not fail with "Unknown departments" errors when advisor names or empty lists are passed.
- **D-04:** The existing `departments` field in `SimulationRun` response may remain for wire compatibility but should not reference old department names in visible advisor output.

### Advisor YAML Templates

- **D-05:** Create new YAML templates in `Simulation/templates/` matching the existing schema (`role_title`, `department`, `agent_id`, `behavioral_bias`, `action_scope`, `memory_context_keys`, etc.) for each immigration advisor.
- **D-06:** Founder Immigration track templates (4): `immigration_attorney`, `evidence_coach`, `founder_mentor`, `tax_company_navigator`.
- **D-07:** First 1000 Days track templates (5): `banking_navigator`, `healthcare_navigator`, `housing_navigator`, `tax_navigator`, `local_systems_mentor`.
- **D-08:** `behavioral_bias.primary_kpi` maps to the advisor's primary concern (e.g., `"evidence_completeness"` for evidence_coach, `"timeline_feasibility"` for immigration_attorney).
- **D-09:** `action_scope.permitted` lists domain-appropriate advisory actions (e.g., `flag_evidence_gap`, `identify_timeline_risk`, `recommend_professional_review`).

### Config and Track Mapping

- **D-10:** Add an `advisor_tracks` section to `infra/config.yaml` that maps track names to lists of template IDs:
  ```yaml
  advisor_tracks:
    founder: [immigration_attorney, evidence_coach, founder_mentor, tax_company_navigator]
    first1000: [banking_navigator, healthcare_navigator, housing_navigator, tax_navigator, local_systems_mentor]
  ```
- **D-11:** Add `advisor_track_templates(track: str) -> list[str]` function to `Simulation/config_loader.py` so the swarm and cascade engines can look up templates by track without importing domain constants.
- **D-12:** `_AGENT_IDS` in `org_persona_generator.py` stays as the static list for cascade-mode ordering; swarm mode uses the new `advisor_track_templates()` lookup.

### Fallback Persona Text

- **D-13:** Replace the hardcoded `_DEMO_SCENARIO_FRAGMENT = "marketing budget"` block and all CFO/VP Sales/Ops/HR hard-coded opinion strings in `_fallback_persona` with track + advisor-specific deterministic text.
- **D-14:** Each advisor template has a unique immigration-domain fallback opinion. Founder-track advisors surface visa/evidence/incorporation risks. First-1000-days advisors surface banking, healthcare, housing, tax, or systems-navigation concerns.
- **D-15:** Fallback text must be meaningful for demo use (not generic stubs). It should reference domain-plausible concerns (e.g., "I-140 priority date", "ITIN application", "security deposit laws") rather than placeholder text.

### Frontend Compatibility

- **D-16:** Update `COMPATIBILITY_DEPTS` in `Frontend/app/simulate/page.tsx` to stop passing `['Sales', 'Finance', 'Operations', 'HR']`. Instead pass the track from `state.track` to the API call.
- **D-17:** `startSimulation` in `Frontend/lib/api.ts` should accept an optional `track` parameter and include it in the POST body. `departments` can be dropped or set to an empty/sentinel list.

### Claude's Discretion

- Exact `behavioral_bias` numeric thresholds for each immigration advisor template (e.g., what triggers pushback).
- Whether to keep or remove the `Simulation/templates/` OrgSim YAML files (cfo.yaml etc.) — they can remain for reference and test stability, as long as the new track routing routes away from them.
- Internal field naming for `role_in_decision` (initiator vs reactor) — immigration advisors are all reactors since the user proposes the scenario.
- Whether to add a stub seed report (analogous to `_load_seed_report`) or skip seed reports entirely for immigration advisors (domain metrics differ; a lean stub is fine).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope
- `.planning/ROADMAP.md` — Phase 2 goal, requirements (SIM-01–SIM-04, SAFE-02), success criteria, implementation notes.
- `.planning/REQUIREMENTS.md` — v1 advisor simulation requirements and traceability.
- `.planning/STATE.md` — current project state.

### Existing Code to Modify
- `Backend/api/routes/simulate.py` — `VALID_DEPARTMENTS`, `SimulateRequest.departments` validator, `create_simulation` handler.
- `infra/config.yaml` — department templates mapping; needs `advisor_tracks` section.
- `Simulation/config_loader.py` — `department_templates()` function; needs `advisor_track_templates()` addition.
- `Simulation/org_persona_generator.py` — `_AGENT_IDS`, `_fallback_persona`, `build_all_personas`; needs immigration domain fallback.
- `Simulation/swarm/persona_pool.py` — `_template_ids_for_departments`; needs track-based lookup.
- `Frontend/app/simulate/page.tsx` — `COMPATIBILITY_DEPTS`, `startSimulation` call.
- `Frontend/lib/api.ts` — `startSimulation` signature; add optional `track` param.

### New Files to Create
- `Simulation/templates/immigration_attorney.yaml`
- `Simulation/templates/evidence_coach.yaml`
- `Simulation/templates/founder_mentor.yaml`
- `Simulation/templates/tax_company_navigator.yaml`
- `Simulation/templates/banking_navigator.yaml`
- `Simulation/templates/healthcare_navigator.yaml`
- `Simulation/templates/housing_navigator.yaml`
- `Simulation/templates/tax_navigator.yaml`
- `Simulation/templates/local_systems_mentor.yaml`

### Prior Phase Context
- `.planning/phases/01-product-shell-and-intake/01-CONTEXT.md` — prior decisions (track names, advisor preview labels, frontend patterns).
- `.planning/phases/01-product-shell-and-intake/01-VERIFICATION.md` — what Phase 1 delivered; confirms COMPATIBILITY_DEPTS shim is still in place.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Simulation/templates/*.yaml`: existing YAML schema is the template contract — new advisor YAMLs must match this schema exactly so `_load_template()`, `build_persona()`, and `build_synthetic_swarm_persona()` work without changes.
- `Simulation/org_persona_generator.py:_load_template()`: reads any YAML from `templates/`; will work for new advisor templates immediately.
- `Simulation/config_loader.py:load_orgsim_config()`: YAML-over-defaults pattern — adding `advisor_tracks` to `infra/config.yaml` is enough; just add a getter.
- `Simulation/swarm/persona_pool.py:build_swarm_personas()`: already accepts `departments: list[str]` and maps via `department_templates()`. Can be adapted to accept a `track` param or fall back gracefully.

### Established Patterns
- DSPy `Predict` signatures are defined inline in `org_persona_generator.py`; they work for any domain text, no changes needed.
- Fallback personas are purely rule-based strings — immigration domain text is a drop-in replacement.
- `infra/config.yaml` is read at startup with YAML-over-defaults merging — safe to extend without breaking existing keys.
- The `departments` field is validated by a `field_validator` in `SimulateRequest` — easiest to relax is to expand the allowed set or make validation conditional on `track`.

### Integration Points
- Frontend → Backend: `POST /simulate` with `{decision, departments, engine, rounds}`. Adding `track` here is a non-breaking additive change.
- Backend → Simulation service: `run_live_streaming_pipeline(departments=...)` in `api/services/live_simulation.py` — this call feeds department names into the Simulation service; it will need to pass `track` or an advisor list.
- Simulation service → persona pool: `build_swarm_personas(scenario, departments, swarm_size)` — `departments` here maps to template IDs via `department_templates()`; the track-based lookup replaces this.

</code_context>

<specifics>
## Specific Ideas

- The Phase 1 advisor preview (D-12, D-13 in 01-CONTEXT.md) already names the exact advisor labels: Founder track = Immigration Attorney, Evidence Coach, Founder Mentor, Tax/Company Navigator; First 1000 Days = Banking, Healthcare, Housing, Tax, Local Systems. Template IDs should snake_case match these labels.
- The demo must run without cloud credentials — the fallback persona text is the primary user experience in that path; it must read convincingly, not as placeholder stubs.
- Keep OrgSim YAML templates intact (do not delete) — existing tests reference them and they don't cause harm if the new track routing bypasses them.

</specifics>

<deferred>
## Deferred Ideas

- Seed report generation for immigration advisors (analogous to `Backend/loaders/` department seed reports) — out of scope for Phase 2; immigration advisors can use a lean stub or no seed report.
- Adding a `rights_advocate` or `credit_navigator` to the First 1000 Days track — useful, but 5 advisors are sufficient for v1 demo.
- Per-track round and swarm_size tuning in config — Claude's discretion for now; defaults (swarm_size=24, max_active=8) work fine.
- TypeDB knowledge graph enrichment for immigration domain — v2 item per REQUIREMENTS.md Out of Scope.

</deferred>

---

*Phase: 02-advisor-simulation-conversion*
*Context gathered: 2026-05-09*

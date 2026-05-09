# Phase 2: Advisor Simulation Conversion - Research

**Researched:** 2026-05-09
**Domain:** Python (FastAPI + Pydantic + YAML + DSPy), TypeScript (Next.js App Router)
**Confidence:** HIGH — all findings derived from direct codebase inspection

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**API Compatibility Strategy**
- D-01: Add optional `track: Literal["founder", "first1000"] | None` field to `SimulateRequest` in `Backend/api/routes/simulate.py`.
- D-02: When `track` is provided, backend auto-selects advisor templates for that track; `departments` validation relaxed (made optional or expanded to accept advisor names). Frontend passes `track` instead of `COMPATIBILITY_DEPTS`.
- D-03: `VALID_DEPARTMENTS` replaced or supplemented so runs do not fail with "Unknown departments" when advisor names or empty lists are passed.
- D-04: `departments` field in `SimulationRun` response may remain for wire compatibility but should not reference old department names in visible advisor output.

**Advisor YAML Templates**
- D-05: Create new YAML templates in `Simulation/templates/` matching the existing schema.
- D-06: Founder Immigration track (4): `immigration_attorney`, `evidence_coach`, `founder_mentor`, `tax_company_navigator`.
- D-07: First 1000 Days track (5): `banking_navigator`, `healthcare_navigator`, `housing_navigator`, `tax_navigator`, `local_systems_mentor`.
- D-08: `behavioral_bias.primary_kpi` maps to advisor's primary concern (e.g., `"evidence_completeness"` for evidence_coach, `"timeline_feasibility"` for immigration_attorney).
- D-09: `action_scope.permitted` lists domain-appropriate advisory actions (e.g., `flag_evidence_gap`, `identify_timeline_risk`, `recommend_professional_review`).

**Config and Track Mapping**
- D-10: Add `advisor_tracks` section to `infra/config.yaml` mapping track names to lists of template IDs.
- D-11: Add `advisor_track_templates(track: str) -> list[str]` function to `Simulation/config_loader.py`.
- D-12: `_AGENT_IDS` in `org_persona_generator.py` stays as static list for cascade-mode ordering; swarm mode uses new `advisor_track_templates()` lookup.

**Fallback Persona Text**
- D-13: Replace `_DEMO_SCENARIO_FRAGMENT = "marketing budget"` block and all CFO/VP Sales/Ops/HR hardcoded opinion strings in `_fallback_persona` with track + advisor-specific deterministic text.
- D-14: Each advisor template has a unique immigration-domain fallback opinion.
- D-15: Fallback text must be meaningful for demo — reference domain-plausible concerns (e.g., "I-140 priority date", "ITIN application", "security deposit laws").

**Frontend Compatibility**
- D-16: Update `COMPATIBILITY_DEPTS` in `Frontend/app/simulate/page.tsx` to stop passing `['Sales', 'Finance', 'Operations', 'HR']`. Instead pass `track` from `state.track`.
- D-17: `startSimulation` in `Frontend/lib/api.ts` accepts optional `track` parameter and includes it in POST body. `departments` can be dropped or set to empty/sentinel list.

### Claude's Discretion

- Exact `behavioral_bias` numeric thresholds for each immigration advisor template.
- Whether to keep or remove `Simulation/templates/` OrgSim YAML files (cfo.yaml etc.).
- Internal field naming for `role_in_decision` (initiator vs reactor) — immigration advisors are all reactors.
- Whether to add a stub seed report or skip seed reports entirely for immigration advisors.

### Deferred Ideas (OUT OF SCOPE)

- Seed report generation for immigration advisors (analogous to `Backend/loaders/` department seed reports).
- Adding `rights_advocate` or `credit_navigator` to First 1000 Days track.
- Per-track round and swarm_size tuning in config.
- TypeDB knowledge graph enrichment for immigration domain.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SIM-01 | Founder Immigration simulations use immigration/founder advisor personas instead of business department personas | D-05, D-06, D-10, D-11 — new YAML templates + track routing replaces department-based dispatch |
| SIM-02 | Learning to be American simulations use banking, credit, healthcare, housing, tax, rights, and local-systems advisor personas | D-07, D-10, D-11 — 5 First 1000 Days templates + track routing |
| SIM-03 | Simulation events stream live to the frontend using the existing WebSocket flow | Pipeline is intact; only `departments` param changes at the API boundary — no WebSocket changes needed |
| SIM-04 | Simulation can complete in demo mode without requiring cloud API keys or all optional infrastructure services | D-13–D-15 — fallback persona rewrite is the primary demo path; must produce immigration-domain text |
| SAFE-02 | Existing business-demo fallback text is removed from visible immigration flows | D-13 — `_DEMO_SCENARIO_FRAGMENT = "marketing budget"` block and all CFO/VP Sales/Ops/HR opinion strings must be replaced |
</phase_requirements>

---

## Summary

Phase 2 is a domain substitution, not an architectural change. The FastAPI → Simulation service → WebSocket → Frontend pipeline is complete and working. The only things that change are: (1) the set of YAML persona templates that feed the simulation, (2) the routing logic that maps a `track` string to template IDs, (3) the fallback opinion text that drives the no-LLM demo path, and (4) the API validation and frontend call that wire the track parameter through.

The critical path is: YAML templates → `config.yaml` mapping → `config_loader.py` getter → `persona_pool.py` routing → `org_persona_generator.py` fallback text → `simulate.py` validation → `api.ts` + `page.tsx` frontend call. Every one of these files has been read; the exact edit points are known.

**Primary recommendation:** Write all 9 YAML templates first, add `advisor_tracks` to config, add the getter, then update validation and fallback in a single coordinated pass. Frontend changes are last and trivial.

---

## Standard Stack

### Core (already installed — no new dependencies)

| Component | Version | Purpose | Notes |
|-----------|---------|---------|-------|
| FastAPI | existing | REST API layer | `SimulateRequest` is a Pydantic `BaseModel` with `field_validator` |
| Pydantic v2 | existing | Request validation | `field_validator` with `@classmethod` pattern used throughout |
| PyYAML | existing | Template loading | `yaml.safe_load` in `_load_template()` |
| DSPy | existing | LLM persona generation | Falls back gracefully to `_fallback_persona()` |
| Next.js App Router | existing | Frontend | TypeScript strict mode, no `any` |

**No new packages required for Phase 2.** [VERIFIED: codebase inspection]

---

## Architecture Patterns

### YAML Template Schema (the contract)

All 9 new templates must conform exactly to this schema so `_load_template()`, `build_persona()`, and `build_synthetic_swarm_persona()` work without modification. [VERIFIED: codebase inspection of all 4 existing templates]

```yaml
role_title: "Immigration Attorney"        # str — displayed in UI agent feed
department: "Founder Immigration"         # str — used in conflict detection dept_a/dept_b labels
agent_id: "immigration_attorney"          # str — snake_case, unique, used as template filename stem

data_scope:
  read: [visa_timeline_data, case_evidence, uscis_processing_times]
  deny: [financial_records_detail]

action_scope:
  permitted: [flag_evidence_gap, identify_timeline_risk, recommend_professional_review, flag_status_conflict]
  forbidden: [guarantee_outcome, predict_approval]

behavioral_bias:
  primary_kpi: "timeline_feasibility"     # str — used in fallback persona text and DSPy inputs
  risk_tolerance: "low"                   # "low" | "medium" | "high"
  pushback_triggers:
    - evidence_gaps_detected: true
    - priority_date_retrogression: true
  alignment_triggers:
    - strong_evidence_package: true
    - timeline_buffer_gt_months: 6

memory_context_keys: [priority_date, filing_deadline, evidence_checklist_status]

reaction_speed: "deliberate"              # "fast" | "medium" | "deliberate"
influence_level: "high"                   # "low" | "medium" | "high" | "very_high"
budget_authority_usd: 0                   # immigration advisors: 0 (not budget holders)
reports_to_count: 0
communication_style: "analytical"         # "direct" | "analytical" | "collaborative"
```

[VERIFIED: schema derived from cfo.yaml, vp_sales.yaml, ops_lead.yaml, hr_director.yaml]

### Track Routing Pattern

The existing `_template_ids_for_departments()` in `persona_pool.py` does a config map lookup: `dept_name → template_id`. The new pattern adds a parallel lookup: `track_name → [template_id, ...]`. The `build_swarm_personas()` function accepts `departments: list[str]` — the cleanest approach is to pass template IDs directly when a track is active, bypassing the dept→template map. [VERIFIED: persona_pool.py inspection]

```
                        track="founder"
                              │
                advisor_track_templates("founder")    ← new function in config_loader.py
                              │
                ["immigration_attorney", "evidence_coach",
                 "founder_mentor", "tax_company_navigator"]
                              │
                _load_template(tid) for each tid       ← existing, unchanged
                              │
                build_synthetic_swarm_persona(...)     ← existing, unchanged
```

### Pipeline Integration Points (all confirmed)

1. **Frontend → Backend POST /simulate**
   - Current: `{decision, departments: ["Sales","Finance","Operations","HR"], engine, rounds}`
   - After Phase 2: `{decision, track: "founder", engine, rounds}` — `departments` omitted or `[]`
   - Location: `Frontend/lib/api.ts` `startSimulation()` + `Frontend/app/simulate/page.tsx` `handleRun()`

2. **Backend → Simulation service POST /generate-personas**
   - Current: `{decision, departments: ["Sales","Finance","Operations","HR"]}`
   - After Phase 2: `{decision, departments: ["immigration_attorney", "evidence_coach", ...]}` — template IDs passed as dept list, OR empty list (which triggers `build_all_personas()` fallback — but that uses `_AGENT_IDS`, so we need the template IDs path)
   - Location: `Backend/api/services/live_simulation.py` `run_live_streaming_pipeline()` — needs to accept and forward `track` or resolve to template IDs before the HTTP call
   - The `GeneratePersonasRequest.departments` in `Simulation/app.py` maps depts via `department_templates()`. Passing advisor template IDs directly will fail because `department_templates()` maps department names like "Sales" → "vp_sales", not advisor IDs → advisor IDs. **This is the key integration risk.**

3. **Simulation service → persona pool**
   - `build_swarm_personas(scenario, departments, swarm_n)` calls `_template_ids_for_departments(departments)` which does `mapping.get(dept)` against the department_templates map. Immigration advisor IDs are not in that map — they will fall through to the hardcoded `["cfo", "vp_sales", "ops_lead", "hr_director"]` default.
   - Fix: either (a) add advisor template IDs to `department_templates` in config, or (b) pass template IDs directly and update `_template_ids_for_departments` to pass them through when they are already template IDs.

### The `generate_personas` Routing Problem (Critical Pitfall)

`Simulation/app.py` `generate_personas()` does:
```python
dept_map = department_templates()
for dept in req.departments:
    aid = dept_map.get(dept)   # "Sales" → "vp_sales"
```

If `req.departments` contains `["immigration_attorney", "evidence_coach"]`, `dept_map.get("immigration_attorney")` returns `None` and those advisors are silently skipped. The fallback then calls `build_all_personas()` with `_AGENT_IDS = ["cfo", "vp_sales", "ops_lead", "hr_director"]`.

**Two clean solutions:**

Option A (preferred per D-10/D-11): Add `advisor_tracks` to `config.yaml`, resolve track → template IDs in `Backend/api/services/live_simulation.py` before calling `/generate-personas`, pass the resolved template IDs as `departments`. Then update `_template_ids_for_departments` in `persona_pool.py` to pass through IDs that don't appear in the dept map (identity fallback). This keeps `Simulation/app.py` unchanged.

Option B: Add advisor IDs as keys in `department_templates` mapping in config (e.g., `immigration_attorney: immigration_attorney`). Simpler but conflates two concepts.

Option A is cleaner and aligns with D-11.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | `yaml.safe_load` (already in use) | Existing `_load_template()` works for any YAML in `templates/` — drop new files in, done |
| Pydantic validation | Custom schema class | Extend existing `SimulateRequest` with `Optional[Literal["founder","first1000"]]` field | Existing `field_validator` pattern handles all edge cases |
| Track-to-template resolution | Hardcoded dict in Python | `infra/config.yaml` + `advisor_track_templates()` getter | Config pattern already established; avoids hardcoding in service code |
| LLM fallback text | Generic stubs | Per-advisor deterministic strings with domain references | The fallback IS the demo UX when no LLM is available (SIM-04) |

---

## Common Pitfalls

### Pitfall 1: `_template_ids_for_departments` silent fallback
**What goes wrong:** When advisor template IDs are passed as `departments` to `build_swarm_personas()`, `_template_ids_for_departments()` finds no matches in `department_templates()` and silently returns `["cfo", "vp_sales", "ops_lead", "hr_director"]`. The simulation runs but produces business-domain personas.
**Why it happens:** The map lookup returns `None` for unknown keys; the `if not seen` fallback kicks in.
**How to avoid:** After adding advisor track templates to config, update `_template_ids_for_departments` to include an identity pass-through: if a `dept` string is not in the dept map but exists as a template file, use it directly.
**Warning signs:** Simulation events show agent `dept` values like "Finance" or "Sales" after a founder track run.

### Pitfall 2: `build_all_personas()` default path uses `_AGENT_IDS`
**What goes wrong:** If `departments` is empty list in `/generate-personas`, `Simulation/app.py` calls `build_all_personas()` which iterates `_AGENT_IDS = ["cfo", "vp_sales", "ops_lead", "hr_director"]`. This produces 4 business-domain personas for any immigration track run.
**Why it happens:** The empty-list path was designed as a "use all defaults" convenience.
**How to avoid:** Always pass resolved template IDs (never empty list) when calling `/generate-personas` from the backend. Do not rely on the empty-list fallback path for immigration tracks.
**Warning signs:** Agent names in the feed show "CFO", "VP of Sales" etc.

### Pitfall 3: `_fallback_persona` `_DEMO_SCENARIO_FRAGMENT` guard
**What goes wrong:** The fallback opinion for non-initiator personas is gated on `"marketing budget" in scenario_lower`. For immigration scenarios, this condition is always `False`, so every advisor falls into the generic final `else` branch: "I support/oppose this proposal. As {role}, my primary concern is {kpi}." This is visibly generic and breaks SIM-04 / SAFE-02.
**Why it happens:** Role-specific opinions were only written for the original marketing-budget demo.
**How to avoid:** Rewrite `_fallback_persona` to dispatch on `template["agent_id"]` (or `department`) rather than on scenario text. Each of the 9 advisor templates needs its own opinion string.

### Pitfall 4: `user_id` computation in `build_persona`
**What goes wrong:** `"user_id": _AGENT_IDS.index(agent_id) if agent_id in _AGENT_IDS else 99` — all 9 immigration advisors fall into the `else 99` branch, so every cascade-mode persona gets `user_id=99`. This may cause collision issues in cascade mode if it matters for ordering.
**Why it happens:** `_AGENT_IDS` only contains the 4 original agent IDs.
**How to avoid:** Per D-12, `_AGENT_IDS` stays as-is for cascade mode; swarm mode uses `advisor_track_templates()`. For cascade mode with immigration advisors, the `user_id=99` collision is acceptable since immigration advisors are all reactors (D-Claude's Discretion). Verify cascade mode is not used in demo flows.

### Pitfall 5: `departments` field in `SimulationRun` response
**What goes wrong:** `create_simulation` stores `req.departments` in the run dict and returns it in `SimulationRun.departments`. After Phase 2, the frontend passes `track` (not departments), so `departments` will be `[]` or absent in the response. Frontend code that reads `run.departments` will get an empty array.
**Why it happens:** The `SimulationRun` schema has a required `departments: list[str]` field.
**How to avoid:** When `track` is provided and `departments` is empty/absent, the backend can store `departments=[]` for wire compat (D-04). Verify the frontend does not render `departments` values anywhere visible.

### Pitfall 6: Pydantic `field_validator` rejects empty `departments`
**What goes wrong:** Current `departments_valid` raises `ValueError("departments must contain at least one entry")` for an empty list. If the frontend sends `departments: []` (or omits it), the API returns 422.
**Why it happens:** The validator enforces non-empty.
**How to avoid:** When `track` is present, the validator must skip or relax the emptiness check. Options: (a) make `departments` optional (`list[str] | None = None`) and skip the validator when `track` is set, (b) compute effective departments from `track` inside the validator (which has access to all values via `model_validator`), or (c) use `@model_validator(mode="after")` to check the combination. Pattern (a) is simplest.

---

## Code Examples

### Existing field_validator pattern to extend
```python
# Source: Backend/api/routes/simulate.py (verified)
@field_validator("departments")
@classmethod
def departments_valid(cls, v: list[str]) -> list[str]:
    invalid = set(v) - VALID_DEPARTMENTS
    if invalid:
        raise ValueError(f"Unknown departments: {invalid}. Valid: {VALID_DEPARTMENTS}")
    if not v:
        raise ValueError("departments must contain at least one entry")
    return v
```

After Phase 2, replace with a `@model_validator(mode="after")` that checks: if `track` is provided → departments validation is skipped; if `departments` provided without `track` → existing check applies.

### Existing config loader pattern to extend
```python
# Source: Simulation/config_loader.py (verified)
def department_templates() -> dict[str, str]:
    sec = simulation_section()
    raw = sec.get("department_templates") or {}
    return {str(k): str(v) for k, v in raw.items()}
```

New function follows the same pattern:
```python
def advisor_track_templates(track: str) -> list[str]:
    cfg = load_orgsim_config()
    tracks = cfg.get("advisor_tracks") or {}
    result = tracks.get(track)
    if not result:
        logger.warning("Unknown advisor track %r — returning empty list", track)
        return []
    return [str(tid) for tid in result]
```

### YAML-over-defaults merge in config_loader
The config loader merges `infra/config.yaml` over defaults with:
```python
sim = {**base.get("simulation", {}), **(loaded.get("simulation") or {})}
base = {**base, **loaded, "simulation": sim}
```
Note: `advisor_tracks` lives at the **top level** of `config.yaml` (not inside `simulation:`), so it will be merged via `{**base, **loaded, ...}` automatically without changing the loader. [VERIFIED: config_loader.py merge logic]

### Frontend: adding `track` to the API call
```typescript
// Source: Frontend/lib/api.ts (verified) — current signature:
export async function startSimulation(
  decision: string,
  departments: string[],
  options?: SimulationStartOptions
): Promise<SimulationCreateResponse>

// After Phase 2:
export async function startSimulation(
  decision: string,
  options?: SimulationStartOptions & { track?: 'founder' | 'first1000' }
): Promise<SimulationCreateResponse>
// or keep departments param and add track to SimulationStartOptions
```

The `SimulationCreateResponse` interface has `departments: string[]` — this must remain for backward compat but the planner should note the frontend does not render this field.

### Fallback persona dispatch pattern
```python
# Source: Simulation/org_persona_generator.py (verified — current anti-pattern)
_DEMO_SCENARIO_FRAGMENT = "marketing budget"
if _DEMO_SCENARIO_FRAGMENT in scenario_lower:
    if agent_id == "vp_sales":
        ...
    elif agent_id == "ops_lead":
        ...
```

Replace with:
```python
# New pattern: dispatch on agent_id only, no scenario sniffing
_FALLBACK_OPINIONS: dict[str, str] = {
    "immigration_attorney": "...",
    "evidence_coach": "...",
    # etc.
}
initial_opinion = _FALLBACK_OPINIONS.get(agent_id, _generic_fallback(role, kpi, is_opposed))
```

---

## Architecture Patterns (File-by-File Edit Map)

### Files to CREATE (9 YAML templates)

Each file lives in `Simulation/templates/{agent_id}.yaml`. Template IDs and track assignments are locked by D-06/D-07.

| File | Track | Primary KPI | Risk Tolerance | Comm Style |
|------|-------|-------------|----------------|------------|
| `immigration_attorney.yaml` | founder | `timeline_feasibility` | low | analytical |
| `evidence_coach.yaml` | founder | `evidence_completeness` | medium | collaborative |
| `founder_mentor.yaml` | founder | `runway_and_pathway_alignment` | high | direct |
| `tax_company_navigator.yaml` | founder | `compliance_risk` | low | analytical |
| `banking_navigator.yaml` | first1000 | `account_access` | medium | direct |
| `healthcare_navigator.yaml` | first1000 | `coverage_continuity` | low | collaborative |
| `housing_navigator.yaml` | first1000 | `housing_stability` | medium | direct |
| `tax_navigator.yaml` | first1000 | `tax_compliance` | low | analytical |
| `local_systems_mentor.yaml` | first1000 | `systems_access` | medium | collaborative |

### Files to MODIFY (7 files)

| File | Change | Key Lines |
|------|--------|-----------|
| `infra/config.yaml` | Add `advisor_tracks:` section at top level | After existing `departments:` block |
| `Simulation/config_loader.py` | Add `advisor_track_templates(track)` function | After `department_templates()` |
| `Simulation/org_persona_generator.py` | Replace `_fallback_persona` dispatch; replace `_DEMO_SCENARIO_FRAGMENT` block | Lines 381–428 |
| `Simulation/swarm/persona_pool.py` | Update `_template_ids_for_departments` with identity pass-through | Lines 22–31 |
| `Backend/api/routes/simulate.py` | Add `track` field to `SimulateRequest`; relax `departments` validator | Lines 22–49 |
| `Backend/api/services/live_simulation.py` | Accept and forward `track`; resolve to template IDs before `/generate-personas` call | Lines 63–103 |
| `Frontend/lib/api.ts` | Add `track` to `startSimulation` signature and POST body | Lines 37–62 |
| `Frontend/app/simulate/page.tsx` | Replace `COMPATIBILITY_DEPTS` usage with `track` in `handleRun()` | Lines 21, 259–264 |

Note: `Simulation/app.py` `/generate-personas` route does NOT need changes — it accepts template IDs as dept strings when `_template_ids_for_departments` is updated with the identity pass-through.

---

## Don't Hand-Roll (Reconfirmed)

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Immigration domain text | Generic filler | Domain-specific references: "I-140 priority date", "ITIN application", "USCIS processing time estimate", "security deposit laws by state", "CHIP/Medicaid eligibility", "ITIN vs SSN bank account requirements" |
| New API layer for track routing | New endpoint | Extend existing `POST /simulate` with optional `track` field |
| New template loader | Custom YAML reader | Existing `_load_template(agent_id)` — drop file in `templates/`, done |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `advisor_tracks` at top level of `config.yaml` is merged by the existing loader without code changes | Architecture Patterns | Low — verified merge logic: `{**base, **loaded, "simulation": sim}` preserves top-level keys |
| A2 | `Simulation/app.py` `/generate-personas` will correctly dispatch to immigration advisor templates when template IDs are passed as `departments` after the `_template_ids_for_departments` identity pass-through | Common Pitfalls | Medium — depends on whether `department_templates()` lookup is in `app.py` itself or only in `persona_pool.py`. Verified: `app.py` also calls `dept_map.get(dept)` directly in `generate_personas()` (lines 226–230). Identity pass-through in `persona_pool.py` alone is not sufficient. |
| A3 | Immigration advisors as "all reactors" means `user_id=99` collision in cascade mode is harmless for demo | Common Pitfalls | Low — cascade mode is secondary; swarm is the default engine |

**A2 requires attention from the planner.** `Simulation/app.py` `generate_personas()` has its own `dept_map.get(dept)` lookup that silently drops advisor IDs. The fix needs to happen there too, not just in `persona_pool.py`. Best approach: also add advisor template IDs to `department_templates` in config as identity mappings (Option B from above, as a supplement to Option A), OR pass advisor template IDs through a new field rather than `departments`.

---

## Open Questions

1. **`Simulation/app.py` generate_personas lookup**
   - What we know: `app.py` calls `dept_map.get(dept)` for each item in `req.departments` (line 227–230). This silently drops advisor IDs not in `department_templates`.
   - What's unclear: Should we add advisor IDs to `department_templates` as identity entries (`immigration_attorney: immigration_attorney`), or add a second code path in `app.py` that checks if a dept string is itself a valid template ID?
   - Recommendation: Add identity entries to `department_templates` in `config.yaml` for all 9 advisor IDs. This is the least-invasive change to `Simulation/app.py` and is consistent with D-10 extending config.

2. **`run_live_streaming_pipeline` signature**
   - What we know: Current signature `(run_id, decision, departments, queue, ...)` passes `departments` to `/generate-personas`. After Phase 2 this needs to pass advisor template IDs.
   - What's unclear: Should `live_simulation.py` call `advisor_track_templates()` directly (importing from `Simulation/config_loader.py` via the service's path context), or should `Backend/api/routes/simulate.py` resolve the template IDs and pass them as `departments`?
   - Recommendation: Resolve template IDs in `simulate.py` (where `track` is known) and pass the resolved list as `departments` to `run_live_streaming_pipeline`. This keeps `live_simulation.py` unchanged and avoids cross-service imports.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 2 is code/config changes only. No new external tools, services, CLIs, or runtimes are required. All dependencies (Python 3.11+, FastAPI, Pydantic, PyYAML, DSPy, Next.js, TypeScript) are already installed and confirmed working by Phase 1.

---

## Validation Architecture

`nyquist_validation` is `false` in `.planning/config.json`. This section is omitted.

---

## Security Domain

Phase 2 adds immigration-domain persona text and a `track` field to the simulation API. ASVS V5 (input validation) applies: the `track` field is validated by Pydantic `Literal["founder", "first1000"] | None` — no free-form strings accepted. No new authentication, session, access control, or cryptography concerns are introduced.

SAFE-02 specifically requires removing business-demo fallback text from immigration flows. The `_fallback_persona` rewrite (D-13) achieves this. The planner should include a verification step confirming "marketing budget", "CFO", "VP Sales", "Ops", "HR Director" do not appear in any fallback string.

---

## Sources

### Primary (HIGH confidence — direct codebase inspection)
- `Backend/api/routes/simulate.py` — full read; VALID_DEPARTMENTS, SimulateRequest, field_validator, create_simulation handler
- `Backend/api/services/live_simulation.py` — full read; run_live_streaming_pipeline signature, generate-personas call
- `Simulation/app.py` — full read; generate_personas route, dept_map lookup, stream_simulation endpoint
- `Simulation/config_loader.py` — full read; load_orgsim_config, department_templates, merge logic
- `Simulation/org_persona_generator.py` — full read; _fallback_persona, _DEMO_SCENARIO_FRAGMENT, build_persona, build_all_personas, _AGENT_IDS
- `Simulation/swarm/persona_pool.py` — full read; _template_ids_for_departments, build_swarm_personas
- `Simulation/templates/{cfo,vp_sales,ops_lead,hr_director}.yaml` — all 4 read; schema confirmed
- `infra/config.yaml` — full read; department_templates mapping, simulation section
- `Frontend/lib/api.ts` — full read; startSimulation signature and POST body
- `Frontend/app/simulate/page.tsx` — full read; COMPATIBILITY_DEPTS, handleRun, track state
- `.planning/config.json` — nyquist_validation: false confirmed
- `.planning/phases/01-product-shell-and-intake/01-VERIFICATION.md` — Phase 1 deliverables confirmed

### No external research required
Phase 2 is a domain substitution within a known codebase. All patterns, integration points, and constraints were determined by direct file inspection. No library documentation lookup was needed.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly
- Architecture: HIGH — all integration points verified from source
- Pitfalls: HIGH — derived from actual code logic, not assumptions
- Fallback text content: MEDIUM — domain terms (I-140, ITIN, CHIP) are well-established but exact phrasing is at Claude's discretion

**Research date:** 2026-05-09
**Valid until:** Stable indefinitely (no external dependencies; codebase is local)

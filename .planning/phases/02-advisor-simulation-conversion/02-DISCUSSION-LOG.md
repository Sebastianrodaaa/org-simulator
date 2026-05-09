# Phase 2: Advisor Simulation Conversion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-09
**Phase:** 02-advisor-simulation-conversion
**Mode:** auto (--auto flag)
**Areas discussed:** API Compatibility Strategy, Advisor YAML Templates, Config and Track Mapping, Fallback Persona Text, Frontend Compatibility

---

## API Compatibility Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Add `track` field, relax `departments` | Add optional `track` to SimulateRequest; backend auto-selects advisor templates; departments becomes optional/open | ✓ |
| Expand VALID_DEPARTMENTS | Keep departments as transport; add immigration advisor names as valid values | |
| Dual-field backward compat | Keep departments required; add track alongside it | |

**Auto-selected:** Add `track` field, relax `departments` (recommended — minimizes frontend changes, cleanest domain model)
**Notes:** Frontend currently sends hardcoded `COMPATIBILITY_DEPTS = ['Sales', 'Finance', 'Operations', 'HR']` as a shim. Replacing with `track` is a one-line fix.

---

## Advisor YAML Templates

| Option | Description | Selected |
|--------|-------------|----------|
| Full YAML templates matching existing schema | New templates follow cfo.yaml structure exactly — preserves DSPy + fallback pipeline | ✓ |
| Simplified schema | New templates with fewer fields; would require `_load_template()` to handle missing keys | |

**Auto-selected:** Full YAML templates matching existing schema (recommended — zero pipeline changes needed)
**Notes:** 9 new templates total: 4 for Founder track, 5 for First 1000 Days track. IDs snake_case match Phase 1 advisor preview labels.

---

## Config and Track Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| `advisor_tracks` section in config.yaml + getter in config_loader | Consistent with existing `department_templates` pattern | ✓ |
| Hardcode in persona_pool.py | Faster but not configurable | |

**Auto-selected:** config.yaml extension with `advisor_tracks` section (recommended — consistent pattern, no magic constants in code)

---

## Fallback Persona Text

| Option | Description | Selected |
|--------|-------------|----------|
| Track + advisor-specific deterministic text | Each advisor has a unique immigration-domain fallback opinion | ✓ |
| Generic immigration fallback | One fallback string for all advisors | |
| No fallback (require cloud LLM) | Demo requires OpenAI key | |

**Auto-selected:** Track + advisor-specific deterministic fallback per advisor (recommended — demo quality without cloud credentials)
**Notes:** Must reference domain-plausible details (priority dates, ITIN, security deposits, etc.) to be credible.

---

## Frontend Compatibility

| Option | Description | Selected |
|--------|-------------|----------|
| Pass `track` to API, drop COMPATIBILITY_DEPTS | One-line change in simulate/page.tsx | ✓ |
| Keep COMPATIBILITY_DEPTS, add track alongside | Two fields in payload | |

**Auto-selected:** Pass `track` to API, drop `COMPATIBILITY_DEPTS` (recommended — removes last OrgSim business-dept shim from frontend)

---

## Claude's Discretion

- Exact behavioral_bias numeric thresholds for immigration advisor templates
- Whether to delete old OrgSim YAML templates (decided: keep them)
- `role_in_decision` handling for immigration advisors (all reactors)
- Seed report stub strategy for immigration advisors

## Deferred Ideas

- Seed report generation for immigration advisors
- `rights_advocate` and `credit_navigator` additional advisors
- Per-track swarm size tuning
- TypeDB immigration domain enrichment (v2)

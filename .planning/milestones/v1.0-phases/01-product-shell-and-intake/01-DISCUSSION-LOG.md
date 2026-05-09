# Phase 1: Product Shell and Intake - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-09
**Phase:** 1-Product Shell and Intake
**Areas discussed:** First Screen Routing, Track + Scenario Defaults, Structured Facts Intake, Pre-run Right Panel

---

## First Screen Routing

| Option | Description | Selected |
|--------|-------------|----------|
| Send `/` to `/simulate` | App opens directly on the CivicBridge rehearsal tool; strongest for hackathon demo. | ✓ |
| Repurpose `/dashboard` into an overview | Keep `/` -> `/dashboard`, but make dashboard a compact CivicBridge overview. | |
| Keep dashboard hidden for now | `/` -> `/simulate`, leave `/dashboard` accessible but lower priority. | |
| You decide | Planner chooses fastest path that satisfies UI-SPEC. | |

**User's choice:** Send `/` to `/simulate`.
**Notes:** User then selected leaving `/dashboard` accessible but not primary; nav should foreground `Rehearse`.

---

## Track + Scenario Defaults

| Option | Description | Selected |
|--------|-------------|----------|
| Founder Immigration | Strong founder-track hook; default scenario can showcase visa/company strategy. | ✓ |
| First 1000 Days | Broader audience; default scenario showcases everyday systems navigation. | |
| No track preselected | User must choose before scenario fields populate. | |
| You decide | Planner chooses best default for demo impact. | |

**User's choice:** Founder Immigration.
**Notes:** User selected scenario cards that populate the form, including textarea and key facts.

---

## Structured Facts Intake

| Option | Description | Selected |
|--------|-------------|----------|
| Mixed compact fields + chips | Text fields for facts like status/deadline/location, chips for uncertainty/privacy constraints. | ✓ |
| Mostly chips | Fast and friendly, but less precise for founder/company facts. | |
| Mostly text fields | Precise, but risks feeling like a legal form. | |
| You decide | Planner chooses. | |

**User's choice:** Mixed compact fields + chips.
**Notes:** User selected all six UI-SPEC fields: Current status, Goal, Deadline, Location, Work/company facts, Family/dependents.

---

## Pre-run Right Panel

| Option | Description | Selected |
|--------|-------------|----------|
| Static advisor/risk map preview | Preserves current visual identity and previews the simulation experience. | ✓ |
| Checklist-style preview | Shows what the app will do step-by-step; clearer but less novel. | |
| Two-tab preview | Advisor map plus action checklist; richer but more work. | |
| You decide | Planner chooses. | |

**User's choice:** Static advisor/risk map preview.
**Notes:** User selected advisor-perspective nodes. Founder track nodes should include Immigration Attorney, Evidence Coach, Founder Mentor, Tax/Company Navigator. First 1000 Days nodes should include Banking, Healthcare, Housing, Tax, Local Systems.

---

## the agent's Discretion

- Exact component extraction boundaries.
- Whether to keep backend payload compatibility shims in Phase 1.
- Exact lucide icons within the UI-SPEC-approved set.

## Deferred Ideas

None.

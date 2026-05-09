# Phase 1: Product Shell and Intake - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 turns `/simulate` into the CivicBridge first screen: an immigration-focused two-track rehearsal tool with guided scenarios, structured intake, privacy/legal safety framing, and a pre-run advisor/risk map preview. This phase does not convert backend personas, risk extraction, or reports; those belong to later phases.

</domain>

<decisions>
## Implementation Decisions

### First Screen Routing

- **D-01:** Redirect `/` directly to `/simulate`.
- **D-02:** Keep `/dashboard` accessible, but do not make it primary in nav or the default entry for Phase 1.
- **D-03:** Navigation should foreground the simulator as `Rehearse`.

### Track And Scenario Defaults

- **D-04:** Default selected track is `Founder Immigration`.
- **D-05:** Guided scenario cards should populate the form when selected.
- **D-06:** Scenario cards should fill both the main situation textarea and the structured key facts fields.

### Structured Facts Intake

- **D-07:** Use a mixed compact intake: text fields for factual details, chips for uncertainty/privacy constraints.
- **D-08:** Include all six UI-SPEC key facts fields in Phase 1: Current status, Goal, Deadline, Location, Work or company facts, Family or dependents.
- **D-09:** The intake should feel useful and lightweight, not like a legal form.

### Pre-Run Right Panel

- **D-10:** Before a run starts, the right panel should show a static advisor/risk map preview.
- **D-11:** Preview nodes should represent advisor perspectives, not life systems.
- **D-12:** Founder Immigration preview advisors should include Immigration Attorney, Evidence Coach, Founder Mentor, and Tax/Company Navigator.
- **D-13:** First 1000 Days preview advisors should include Banking, Healthcare, Housing, Tax, and Local Systems.

### the agent's Discretion

- The planner may choose exact component extraction boundaries, provided the UI-SPEC contract is followed.
- The planner may keep backend request fields as compatibility shims in Phase 1 if the user-facing UI hides old department language.
- The planner may choose exact icon choices from `lucide-react` within the UI-SPEC-approved set.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope

- `.planning/ROADMAP.md` — Phase 1 goal, requirements, success criteria, and phase boundary.
- `.planning/REQUIREMENTS.md` — v1 requirements and Phase 1 traceability.
- `.planning/STATE.md` — current project state and next step.

### Design Contract

- `.planning/phases/01-product-shell-and-intake/01-UI-SPEC.md` — approved visual and interaction contract for Phase 1.

### Codebase Context

- `.planning/codebase/STRUCTURE.md` — frontend files and route/component structure.
- `.planning/codebase/CONVENTIONS.md` — established frontend styling, state, and data-shape patterns.
- `.planning/codebase/STACK.md` — Next.js/Tailwind/lucide stack constraints.

### Research Context

- `.planning/research/SUMMARY.md` — product direction, v1 feature set, risk themes, and official-source framing.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `Frontend/app/simulate/page.tsx`: primary split-pane simulation UI to repurpose for CivicBridge.
- `Frontend/components/Nav.tsx`: navigation brand and links to update.
- `Frontend/app/page.tsx`: currently redirects `/` to `/dashboard`; should redirect to `/simulate`.
- `Frontend/app/dashboard/page.tsx`: remains accessible but should not be primary in Phase 1.
- `Frontend/components/SwarmInteractionGraph.tsx`: can inform right-panel advisor map behavior.
- `Frontend/components/ConflictGraph.tsx`: can inform static map layout, though labels should avoid "conflict" in the primary flow.
- `Frontend/lib/types.ts`: current department/conflict types may need UI-facing aliases or track-specific types.
- `Frontend/lib/api.ts`: may keep existing API payload shape if needed for Phase 1 compatibility.

### Established Patterns

- Frontend uses Next.js App Router, local React state, Tailwind utility classes, and compact operational UI.
- Existing simulator uses a full-height split pane with left input/feed and right graph surface.
- Existing event flow is scenario creation -> run ID -> WebSocket stream -> graph/feed updates.
- Current code has business labels hardcoded in UI constants; Phase 1 should replace visible labels and examples.

### Integration Points

- `/simulate` is the primary route for Phase 1 changes.
- `/` redirect must change in `Frontend/app/page.tsx`.
- Nav must point the primary user action to `/simulate` with label `Rehearse`.
- Scenario card selections should update local state for track, situation text, key facts, and uncertainty chips before run creation.

</code_context>

<specifics>
## Specific Ideas

- Product name in UI should be CivicBridge.
- The first screen should be the tool itself, not a marketing page.
- The default demo should showcase the Founder Immigration track.
- The pre-run preview should feel like an advisor-panel rehearsal, not a generic checklist.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Product Shell and Intake*
*Context gathered: 2026-05-09*


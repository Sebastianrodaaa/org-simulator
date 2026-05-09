# Phase 1 Research: Product Shell and Intake

**Phase:** 1 - Product Shell and Intake
**Date:** 2026-05-09
**Status:** Complete

## Research Question

What does the planner need to know to implement the Phase 1 CivicBridge frontend conversion cleanly within the existing OrgSim app?

## Key Findings

### Existing UI Shape

The current `/simulate` page already has the correct product structure for Phase 1:

- Left panel: scenario input, controls, run CTA, live activity feed.
- Right panel: graph header, interactive graph, legend.
- WebSocket and run-state logic already live in the page and should be preserved.

The plan should change visible product vocabulary and pre-run intake behavior, not rebuild the app.

### Highest-Leverage Files

- `Frontend/app/page.tsx`: change root redirect from `/dashboard` to `/simulate`.
- `Frontend/components/Nav.tsx`: rename brand and nav labels, make `Rehearse` primary.
- `Frontend/app/layout.tsx`: update metadata.
- `Frontend/app/simulate/page.tsx`: central Phase 1 surface.
- `Frontend/lib/types.ts`: add or alias CivicBridge track/intake types if useful.

### UI Implementation Strategy

Use local component extraction inside `Frontend/app/simulate/page.tsx` first. If the file becomes unwieldy, extract small presentational components into `Frontend/components/` during execution, but do not introduce a new design system.

Recommended local structures:

- `type Track = "founder" | "first1000"`
- `type KeyFacts = { currentStatus: string; goal: string; deadline: string; location: string; workCompanyFacts: string; familyDependents: string }`
- `TRACKS` array with labels, accent colors, icons, subtexts, and advisor preview nodes.
- `GUIDED_SCENARIOS` array keyed by track, with situation text, key facts, selected unknown chips, and advisor preview copy.
- `UNCERTAINTY_CHIPS` array for multi-select.

### Backend Compatibility

Phase 1 is frontend shell/intake. It may continue sending the existing backend `departments` payload as an internal compatibility shim. The UI must not expose Sales/Finance/Operations/HR in the primary flow.

Recommended shim:

- Founder Immigration maps to all four existing departments for now.
- First 1000 Days maps to all four existing departments for now.
- Store this mapping in code with a comment that Phase 2 replaces backend personas/advisors.

### Pre-Run Preview

The right panel should show a static advisor perspective preview before any run ID exists. This can be implemented in JSX/CSS without D3 for speed and layout control. Once a run starts, the existing graph components can continue rendering live events.

Recommended preview shape:

- Center label: selected track or "Your rehearsal".
- Four/five advisor nodes positioned around it.
- Thin neutral connector lines or a simple responsive grid are acceptable.
- Do not use old department colors or labels.

### Copy Safety

The primary flow must avoid legal-outcome promises. Use "rehearsal", "planning aid", "risks", "questions", "next steps", "verify", and "qualified professional".

Forbidden visible primary-flow terms remain:

- OrgSim
- CFO, VP Sales, HR Director, Ops Lead
- Q4 marketing budget
- Sales pipeline
- conflict/conflicts
- approval odds
- you qualify
- guaranteed

## Plan Implications

Use three plans:

1. Routing, navigation, metadata, and shell copy.
2. Track selector, guided scenarios, key facts, chips, and run payload assembly.
3. Static advisor preview, empty/running labels, responsive polish, and visible-copy verification.

## Validation Architecture

Phase 1 validation should be mostly static and build-oriented:

- `rg -n "OrgSim|CFO|VP Sales|HR Director|Ops Lead|Q4 marketing|Sales pipeline|conflict|approval odds|you qualify|guaranteed" Frontend/app Frontend/components Frontend/lib`
- `cd Frontend && npm run lint`
- `cd Frontend && npm run build`
- Manual browser check of `/simulate` at desktop and mobile widths if a dev server is started during execution.

## Sources

- `.planning/phases/01-product-shell-and-intake/01-CONTEXT.md`
- `.planning/phases/01-product-shell-and-intake/01-UI-SPEC.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/STACK.md`
- `Frontend/app/simulate/page.tsx`
- `Frontend/components/Nav.tsx`
- `Frontend/app/page.tsx`

## RESEARCH COMPLETE


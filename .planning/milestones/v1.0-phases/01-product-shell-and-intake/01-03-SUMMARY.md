---
phase: 01-product-shell-and-intake
plan: 01-03
subsystem: ui
tags: [nextjs, react, advisor-preview, risk-map]
requires:
  - phase: 01-01
    provides: CivicBridge shell and simulator primary route
provides:
  - Static advisor preview before run
  - Advisor/risk/action-report simulator labels
  - Clean frontend lint/build gate
affects: [phase-01, phase-02, phase-03]
tech-stack:
  added: []
  patterns: [pre-run preview, advisor-language labels]
key-files:
  created:
    - Frontend/components/ConflictGraph.tsx
    - Frontend/components/DeptFeedDrawer.tsx
    - Frontend/components/SwarmInteractionGraph.tsx
    - Frontend/lib/useSimulationStream.ts
  modified:
    - Frontend/app/simulate/page.tsx
    - Frontend/components/ui/agent-plan.tsx
key-decisions:
  - "Preview nodes represent advisor perspectives, not life systems."
  - "Use risk/action-report language for visible simulation output."
patterns-established:
  - "Pre-run right panel mirrors the selected CivicBridge track."
requirements-completed: [SHELL-01, SHELL-02, INTAKE-03, SAFE-01]
duration: 28min
completed: 2026-05-09
---

# Phase 1 Plan 03 Summary

**The right panel now previews advisor perspectives and the live simulator uses risk-map/action-report language.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-05-09T15:30:00Z
- **Completed:** 2026-05-09T15:37:00Z
- **Tasks:** 4
- **Files modified:** 6

## Accomplishments

- Added Founder advisor preview nodes: Immigration Attorney, Evidence Coach, Founder Mentor, and Tax/Company Navigator.
- Added First 1000 Days advisor preview nodes: Banking, Healthcare, Housing, Tax, and Local Systems.
- Replaced visible simulator labels with Advisor Deliberation, Risk Map, Detected risks, and View action report.
- Cleared legacy business copy and React lint blockers in simulator support files.

## Task Commits

1. **Tasks 1-3: Advisor preview and label updates** - `1ca18f9`
2. **Task 4: Verification and lint cleanup** - `65face0`

## Files Created/Modified

- `Frontend/app/simulate/page.tsx` - Static advisor preview and risk/action labels.
- `Frontend/components/ui/agent-plan.tsx` - CivicBridge-oriented live activity plan text and React lint fix.
- `Frontend/components/ConflictGraph.tsx` - Legacy role copy removed from the simulator graph component.
- `Frontend/components/DeptFeedDrawer.tsx` - Legacy role copy removed and React lint fixed.
- `Frontend/components/SwarmInteractionGraph.tsx` - Deterministic node offsets replace render-time randomness.
- `Frontend/lib/useSimulationStream.ts` - Stream reset moved out of synchronous effect body for React lint.

## Decisions Made

Fixed the simulator support lint issues rather than documenting a failing lint gate, because these files are used by the Phase 1 simulator path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Supporting simulator files blocked lint**
- **Found during:** Task 4
- **Issue:** `npm run lint` failed on React 19 rules in simulator support components/hooks and unused legacy imports.
- **Fix:** Converted task derivation to `useMemo`, moved reset state updates into async callbacks, replaced render-time `Math.random`, and removed unused imports.
- **Files modified:** `Frontend/components/ui/agent-plan.tsx`, `Frontend/components/DeptFeedDrawer.tsx`, `Frontend/components/SwarmInteractionGraph.tsx`, `Frontend/lib/useSimulationStream.ts`
- **Verification:** `npm run lint`, `npx tsc --noEmit`, and `npm run build` passed.
- **Committed in:** `65face0`

**2. [Rule 2 - Missing Critical] Legacy business copy remained in simulator support UI**
- **Found during:** Task 4 visible-copy scan
- **Issue:** Support components rendered old role and product language even though the primary simulator shell had been converted.
- **Fix:** Replaced forbidden legacy copy with CivicBridge advisor/risk language.
- **Files modified:** `Frontend/components/ui/agent-plan.tsx`, `Frontend/components/ConflictGraph.tsx`, `Frontend/components/DeptFeedDrawer.tsx`
- **Verification:** Forbidden-copy scan returned no matches.
- **Committed in:** `65face0`

---

**Total deviations:** 2 auto-fixed.
**Impact on plan:** Necessary for the phase static gate and safe visible copy; no unrelated behavior was changed intentionally.

## Issues Encountered

`Frontend` had pre-existing untracked simulator files. Files touched for the Phase 1 simulator path were committed inside the nested frontend repository; unrelated dirty files were left untouched.

## User Setup Required

None.

## Next Phase Readiness

Phase 2 can convert backend agents/advisors knowing the frontend already frames runs as rehearsals with advisor and risk language.

## Self-Check: PASSED

- `rg -n "Swarm Interaction Graph|Org Network|Detected conflicts|View simulation report|Run a scenario to see cascade" app/simulate/page.tsx` returned no matches.
- `rg -n "Risk Map Preview|Advisor Deliberation|Detected risks|View action report" app/simulate/page.tsx` found the expected labels.
- `rg -n "OrgSim|CFO|VP Sales|HR Director|Ops Lead|Q4 marketing|Sales pipeline|approval odds|you qualify|guaranteed" app components lib` returned no matches.
- `npm run lint` passed.
- `npx tsc --noEmit` passed.
- `npm run build` passed.

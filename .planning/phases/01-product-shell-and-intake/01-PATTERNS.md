# Phase 1 Pattern Map

**Phase:** 1 - Product Shell and Intake
**Date:** 2026-05-09

## Files To Modify And Closest Analogs

| Target | Role | Closest existing analog | Pattern to preserve |
|--------|------|-------------------------|---------------------|
| `Frontend/app/page.tsx` | Root redirect | Existing `redirect('/dashboard')` | Keep server redirect simple; change target only |
| `Frontend/components/Nav.tsx` | Top navigation | Existing `links` array and active path check | Keep compact border-bottom nav and active underline |
| `Frontend/app/layout.tsx` | Metadata/app shell | Existing Geist font + `Nav` wrapper | Keep root flex shell and font variables |
| `Frontend/app/simulate/page.tsx` | Main Phase 1 UI | Existing split-pane simulator page | Preserve run state, WebSocket hook, graph/feed conditions |
| `Frontend/lib/types.ts` | CivicBridge UI types | Existing shared TypeScript type file | Add types without breaking existing event mapping |

## Existing Patterns

### Local State

`Frontend/app/simulate/page.tsx` uses local `useState` for decision, selected departments, engine settings, run ID, loading, and errors. Phase 1 should extend this with track, selected scenario, key facts, and selected uncertainty chips.

### Conditional Rendering

The page already conditionally shows demo banner, activity feed, conflicts list, report button, right-panel graph labels, and empty states based on `runId`, `status`, and event-derived data. Phase 1 should reuse the same conditional style.

### Styling

The app uses Tailwind utility classes directly. Common patterns:

- `rounded-md` and `rounded-lg`
- `border border-gray-200`
- `text-xs`/`text-sm` compact labels
- `bg-white`, `bg-gray-50`
- focus rings via `focus:ring-2`

### Graph Surface

The graph area is a full-height right panel with a header and footer legend. Before a run, a static preview can occupy the same graph container instead of rendering `SwarmInteractionGraph`.

## Implementation Hints

- Keep old backend `departments` details internal and invisible in Phase 1.
- Update `localStorage` key from `orgsim_last_run_id` to a CivicBridge key when touching run creation.
- The existing `AgentFeedSkeleton`, `relativeTime`, and `initials` helpers in `simulate/page.tsx` are partially unused; execution may remove or ignore unused helpers if lint complains.
- If a static advisor preview is added, make it a small local component first. Extract only if needed.

## Verification Anchors

- `/` redirect target should be `/simulate`.
- Nav brand should say `CivicBridge`.
- Nav should contain `Rehearse`.
- `/simulate` should contain `Founder Immigration`, `First 1000 Days`, `Run rehearsal`, and the safety note copy.
- Primary pre-run UI should not show old business demo language.


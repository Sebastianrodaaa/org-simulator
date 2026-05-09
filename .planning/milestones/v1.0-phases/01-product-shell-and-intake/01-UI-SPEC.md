---
phase: 1
slug: product-shell-and-intake
status: approved
shadcn_initialized: false
preset: none
created: 2026-05-09
---

# Phase 1 — UI Design Contract

> Visual and interaction contract for Product Shell and Intake. Generated for CivicBridge Simulator, verified inline against the 6 UI dimensions.

---

## Phase Goal

Turn the first screen into an immigration-focused two-track scenario tool. The user should immediately understand that CivicBridge helps rehearse a founder immigration or first-1000-days decision, enter a scenario safely, and prepare to run the existing simulation flow.

## Files In Scope

- `Frontend/app/layout.tsx`
- `Frontend/components/Nav.tsx`
- `Frontend/app/page.tsx`
- `Frontend/app/dashboard/page.tsx`
- `Frontend/app/simulate/page.tsx`
- `Frontend/lib/types.ts`
- `Frontend/lib/api.ts` only if request labels need light adaptation

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none |
| Icon library | lucide-react |
| Font | Geist Sans for UI, Geist Mono only for run IDs/source-like metadata |

Do not introduce shadcn, Radix, or another component system in Phase 1. Use existing Tailwind utility styling and current component structure.

---

## Layout Contract

### Primary Route

`/simulate` is the primary tool surface. It must remain a full-height, split-pane application screen, not a landing page.

Desktop layout:

- Top nav height remains compact, approximately 45-56px.
- Left panel width: 560-620px.
- Right panel fills remaining width.
- Left panel scrolls independently.
- Right panel remains an interactive preview/status surface.

Mobile layout:

- Stack vertically.
- Intake appears first.
- Right panel appears below with minimum height 360px.
- No horizontal scrolling.
- Text in buttons, chips, cards, and banners must wrap or truncate cleanly.

### Left Panel Structure

Order must be:

1. Product/phase header
2. Track segmented control
3. Guided scenario selector
4. Scenario text area
5. Key facts grid
6. Unknowns/constraints selector
7. Privacy/legal safety note
8. Run CTA
9. Live activity area, only after run starts

### Right Panel Structure

Before run:

- Show "Decision Map Preview" or "Risk Map Preview".
- Show compact nodes for the selected track's advisor perspectives/systems.
- Empty state should explain that running a scenario will surface risks and next steps.

During run:

- Reuse existing swarm/graph surface.
- Rename "Swarm Interaction Graph" to "Advisor Deliberation".
- Rename "Org Network" to "Risk Map".
- Rename "conflict" counts to "risk" or "blocker" counts.

---

## Spacing Scale

Declared values, all multiples of 4:

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Inline icon/text gaps, dense metadata gaps |
| sm | 8px | Chip gaps, compact field spacing |
| md | 16px | Form group spacing, default panel padding minimum |
| lg | 24px | Major section padding and split-pane internal spacing |
| xl | 32px | Header-to-form spacing and major empty-state spacing |
| 2xl | 48px | Only for larger dashboard section breaks |
| 3xl | 64px | Avoid in Phase 1 tool surface |

Exceptions: existing graph canvas internals may keep their current fixed dimensions and D3 positioning constants.

Implementation guidance:

- Left panel content padding should be 20px on desktop and 16px on mobile.
- Use `space-y-4` for main form sections.
- Use `space-y-2` or `gap-2` inside compact controls.
- Buttons and inputs should not change layout size on hover/active.

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px | 400 | 1.5 |
| Label | 12px | 600 | 1.35 |
| Heading | 18-20px | 650-700 | 1.25 |
| Panel title | 14px | 650 | 1.35 |
| Display | 24px max | 700 | 1.2 |
| Metadata | 11-12px | 500 | 1.35 |

Rules:

- No hero-scale typography in Phase 1.
- Do not scale font size with viewport width.
- Letter spacing must remain `0` except tiny uppercase metadata labels, which may use Tailwind's existing `tracking-wide` sparingly.
- Use plain language. Avoid legal jargon where a user-facing equivalent exists.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#f8fafc` | App background and right-panel preview background |
| Secondary (30%) | `#ffffff` | Left panel, nav, input surfaces, graph footer/header |
| Primary text | `#111827` | Main text |
| Muted text | `#6b7280` | Hints, metadata, descriptions |
| Border | `#e5e7eb` | Panel, inputs, subtle dividers |
| Accent: Founder | `#0f766e` | Founder track active state, founder advisor nodes |
| Accent: First 1000 Days | `#2563eb` | First-1000-days track active state, systems navigator nodes |
| Warning | `#d97706` | Unknowns, must-verify notes |
| Risk | `#dc2626` | High-risk badges only |
| Destructive | `#dc2626` | Destructive actions only |

Accent reserved for:

- Active track selection.
- Advisor/system node colors.
- Risk severity indicators.
- Focus rings may use neutral `#111827` or the active track accent.

Color rules:

- Avoid the current one-note business palette feel by balancing teal, blue, neutral gray, amber, and red.
- Do not use purple-dominant or gradient-orb decorative backgrounds.
- Risk red must not be used for ordinary active controls.
- Track colors should be visible but not loud; most UI remains neutral.

---

## Core Components

### Track Segmented Control

Purpose: choose between Founder Immigration and Learning to be American.

Contract:

- Two equal-width segments on mobile and desktop.
- Active segment uses track accent background with white text.
- Inactive segment uses white background, neutral border, dark text.
- Include lucide icons:
  - Founder: `Rocket`, `BriefcaseBusiness`, or `Building2`
  - First 1000 Days: `Map`, `Home`, or `Compass`
- Button text:
  - `Founder Immigration`
  - `First 1000 Days`
- Subtext can appear below or inside compact two-line segment:
  - Founder: `Visa, company, work strategy`
  - First 1000 Days: `Banking, health, housing, taxes`

### Guided Scenario Selector

Purpose: load credible demo scenarios.

Contract:

- Use compact selectable rows, not large marketing cards.
- Each row has title, one-line description, and small track-colored indicator.
- Required scenarios:
  - `Founder pathway rehearsal`: founder weighing O-1, EB-1A, International Entrepreneur Rule, company setup, and runway timing.
  - `First 90 days setup`: newcomer planning SSN/ITIN, bank account, credit, health coverage, housing, taxes, and local rights.
- Selected scenario populates the scenario textarea and key facts fields.

### Scenario Textarea

Purpose: freeform user situation.

Contract:

- Label: `Situation`
- Placeholder: `Describe your goal, current status, deadline, location, and what feels uncertain.`
- Minimum height: 120px desktop, 112px mobile.
- Use normal sans font, not mono; immigration situations should feel human, not like code.
- Disabled after run starts.

### Key Facts Grid

Purpose: gather structured facts without becoming a legal form.

Fields:

- `Current status`
- `Goal`
- `Deadline`
- `Location`
- `Work or company facts`
- `Family or dependents`

Contract:

- Desktop: two-column grid in left panel.
- Mobile: single column.
- Each field may be a simple text input or compact textarea.
- Every field accepts empty/unknown state.
- Use `Unknown` toggle/chip where practical instead of forcing text.

### Unknowns/Constraints Selector

Purpose: let users name uncertainty without blocking simulation.

Chips:

- `I am not sure about my status`
- `Deadline is uncertain`
- `I need professional review`
- `Money is tight`
- `I do not know which agency applies`
- `I am worried about sharing details`

Contract:

- Multi-select chips.
- Selected chips use amber-tinted style, not red.
- These chips feed only scenario text in Phase 1 if backend model is not changed yet.

### Safety Note

Purpose: prevent overclaiming and establish trust.

Copy:

`CivicBridge is a planning aid, not legal advice. It helps organize risks, questions, and next steps so you can verify details with official sources or a qualified professional. Avoid entering documents or secrets in this demo.`

Contract:

- Always visible before run.
- Small text, neutral/amber left border.
- Must not be hidden behind a tooltip.

### Primary CTA

Copy:

- Before run: `Run rehearsal`
- Loading: `Starting rehearsal...`
- During run: `Rehearsal running`
- Complete secondary CTA: `View action report`

Contract:

- Full-width in left panel.
- Uses active track accent.
- Disabled when scenario is empty.
- Disabled state must be visually distinct and accessible.

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Product name | CivicBridge |
| Nav brand | CivicBridge |
| Simulate nav | Rehearse |
| Dashboard nav | Overview |
| Primary heading | Rehearse an immigration or first-1000-days decision |
| Supporting copy | Choose a track, describe the situation, and let simulated advisors surface risks, missing facts, and next steps. |
| Track label | Choose a track |
| Scenario selector label | Start from a demo scenario |
| Scenario field label | Situation |
| Key facts label | Key facts |
| Unknowns label | What is uncertain? |
| Empty map heading | No rehearsal running |
| Empty map body | Choose a track and run a scenario to see advisor perspectives, risks, and next steps appear here. |
| Error state | We could not start the rehearsal. Check that the API is running, then try again. |
| Primary CTA | Run rehearsal |
| Report CTA | View action report |
| Safety note | CivicBridge is a planning aid, not legal advice. It helps organize risks, questions, and next steps so you can verify details with official sources or a qualified professional. Avoid entering documents or secrets in this demo. |

Forbidden user-facing copy in Phase 1 primary flow:

- OrgSim
- department, departmental, org health, executive report
- CFO, VP Sales, HR Director, Ops Lead
- Q4 marketing budget
- Sales pipeline
- conflict, conflicts (replace with risk, blocker, tradeoff, or dependency)
- approval odds
- you qualify
- guaranteed

---

## Interaction States

### Before Run

- Track can change.
- Scenario can change.
- Key facts can change.
- Unknown chips can change.
- Right panel shows preview/empty state.

### Running

- Track, scenario, and facts lock to prevent mismatch with run payload.
- Activity feed appears.
- CTA shows running state.
- Live indicator uses green only for connection/run liveness, not success.

### Complete

- CTA to report appears.
- Right panel status says `complete`.
- Risk count uses `risk`/`risks`, not `conflict`.

### Error

- Error text is specific and wraps inside the left panel.
- Do not clear user-entered scenario.
- CTA allows retry if no run ID was created.

---

## Accessibility Contract

- All interactive controls must be reachable by keyboard.
- Segmented control buttons need visible focus rings.
- Icon-only controls are not allowed unless they have `aria-label` and visible tooltip/title; Phase 1 should prefer icon+text.
- Color may not be the only indicator of selected track or risk severity.
- Text contrast must meet WCAG AA for normal text.
- The safety note must be plain text in the DOM.
- The graph must keep a meaningful `aria-label`.

---

## Responsive Contract

Desktop:

- `lg:flex-row`
- Left panel fixed around 580px.
- Right panel fills remaining space.
- Right panel graph area minimum height is viewport minus nav.

Mobile:

- `flex-col`
- Left panel full width.
- Right panel min height 360px.
- Track selector can become two stacked buttons if needed below 360px width.
- Key facts grid becomes single column.
- No text overlap in chips, buttons, or graph header.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not required |
| third-party | none | not allowed in Phase 1 |

No registry components should be added in Phase 1.

---

## Implementation Notes

- Keep existing Tailwind and component architecture.
- Use lucide icons already available through `lucide-react`.
- Prefer semantic variable names in TypeScript such as `Track`, `TRACKS`, `GUIDED_SCENARIOS`, and `RISK_COLORS`.
- Phase 1 may still send the existing `departments` field to the backend if needed for compatibility, but the UI must present these as advisor perspectives, not departments.
- If backend labels cannot be changed until Phase 2, map tracks to existing department arrays internally and hide that implementation detail.
- Replace `localStorage` key `orgsim_last_run_id` with a CivicBridge key when touching that area.
- Do not add a landing page. Redirect `/` may go to `/simulate` instead of `/dashboard` if implementation scope allows.

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-05-09

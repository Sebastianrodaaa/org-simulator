# Research: Pitfalls

**Date:** 2026-05-09
**Project:** CivicBridge Simulator
**Research dimension:** Pitfalls

## Pitfall: Legal Advice Overclaiming

**Risk:** The product may sound like it is giving immigration legal advice or predicting case outcomes.

**Prevention:**

- Use "planning aid" and "not legal advice" language.
- Label outputs as risks, questions, evidence gaps, and next steps.
- Include professional-review triggers.
- Avoid "you qualify" or "you will be approved" wording.

**Phase:** Initial domain conversion and report generation.

## Pitfall: Stale Immigration Facts

**Risk:** Visa thresholds, filing rules, fees, health coverage rules, and tax dates change.

**Prevention:**

- Include source URLs and "last verified" dates for static facts.
- Prefer official government sources.
- Make the simulation ask users to verify deadlines and eligibility with official sources or professionals.

**Phase:** Requirements and report features.

## Pitfall: Shallow Rebrand

**Risk:** UI labels change but fallback text still talks about CFOs, budgets, Sales, and HR.

**Prevention:**

- Replace demo scenarios, persona templates, conflict categories, fallback copy, and tests together.
- Search for old terms before verification.

**Phase:** Frontend and simulation domain conversion.

## Pitfall: Too Much Infrastructure

**Risk:** Hackathon demo becomes hard to run because it depends on every Docker service and local LLM.

**Prevention:**

- Keep a minimal demo path using existing rule-based fallback.
- Make optional services enhance the demo rather than block it.
- Document exact run commands.

**Phase:** Demo readiness.

## Pitfall: Stereotyping "Learning to be American"

**Risk:** The product could feel culturally prescriptive or patronizing.

**Prevention:**

- Frame the track as systems navigation, not assimilation judgment.
- Focus on banking, credit, healthcare, housing, taxes, work, school, rights, and local services.
- Let users choose goals and context.

**Phase:** UX copy and scenario templates.

## Pitfall: Sensitive Data Handling

**Risk:** Users may enter immigration status, family facts, health facts, finances, or employer details.

**Prevention:**

- Avoid storing sensitive documents in v1.
- Keep local/in-memory run history unless persistence is deliberately designed.
- Add privacy-friendly copy near intake.

**Phase:** Intake and reporting.

## Sources

- USCIS entrepreneur options: https://www.uscis.gov/working-in-the-united-states/options-for-alien-entrepreneurs-to-work-in-the-united-states
- USCIS International Entrepreneur Rule: https://www.uscis.gov/working-in-the-united-states/international-entrepreneur-rule
- IRS individual tax filing: https://www.irs.gov/individual-tax-filing
- SSA immigration page: https://www.ssa.gov/people/immigrants/
- HealthCare.gov immigrant coverage: https://www.healthcare.gov/immigrants/lawfully-present-immigrants/
- HUD Fair Housing Act overview: https://www.hud.gov/helping-americans/fair-housing-act-overview


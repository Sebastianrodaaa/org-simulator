# Research Summary

**Date:** 2026-05-09
**Project:** CivicBridge Simulator

## Key Findings

**Stack:** Keep the existing OrgSim stack. The simulation architecture is already the differentiator; the highest-value work is domain conversion and report usefulness.

**Table stakes:** The v1 needs track selection, structured scenario intake, advisor simulation, risk/blocker extraction, official-source-aware caveats, and an action report.

**Watch out for:** Legal advice overclaiming, stale facts, shallow rebrand artifacts, excessive infrastructure, sensitive data handling, and cultural stereotyping.

## Product Direction

CivicBridge should be a life-strategy rehearsal tool, not a legal-answer bot. The user describes a founder immigration or first-1000-days situation. The app runs a panel of simulated advisors, surfaces risk and dependency patterns, and turns the result into an action plan.

## V1 Feature Set

- Combined track selector.
- Two polished demo scenarios:
  - Founder deciding between O-1, EB-1A, International Entrepreneur Rule, H-1B alternatives, and company setup constraints.
  - Newcomer planning first 90 days across SSN/ITIN, bank account, credit, health coverage, housing, taxes, and local rights.
- Advisor personas configured in YAML.
- Risk categories replacing business conflicts.
- Report page with next steps, evidence gaps, caveats, and professional-review questions.
- Reliable fallback mode.

## Architecture Guidance

Do not rebuild. Rename and reshape:

- `departments` -> `advisors` or `perspectives`
- `decision` -> `scenario`
- `conflicts` -> `risks`
- department graph -> systems dependency/risk graph
- executive report -> action plan

## Official Source Themes

- USCIS provides founder-relevant pathway and International Entrepreneur Rule information, including updated threshold concepts.
- IRS/SSA/HealthCare.gov/HUD/CFPB cover key first-1000-days systems: taxes, identifiers, healthcare, housing rights, and banking.
- Many eligibility details depend on status, state, facts, and date; v1 should guide verification rather than claim certainty.

## Sources

- USCIS, Options for Alien Entrepreneurs: https://www.uscis.gov/working-in-the-united-states/options-for-alien-entrepreneurs-to-work-in-the-united-states
- USCIS, International Entrepreneur Rule: https://www.uscis.gov/working-in-the-united-states/international-entrepreneur-rule
- USCIS, O-1 Policy Manual Chapter 4: https://www.uscis.gov/policy-manual/volume-2-part-m-chapter-4
- USCIS, EB-1 employment-based immigration: https://www.uscis.gov/green-card/green-card-eligibility/green-card-for-employment-based-immigrants
- IRS, Individual tax filing: https://www.irs.gov/individual-tax-filing
- IRS, ITIN: https://www.irs.gov/individuals/individual-taxpayer-identification-number
- SSA, Immigration: https://www.ssa.gov/people/immigrants/
- HealthCare.gov, Lawfully present immigrants: https://www.healthcare.gov/immigrants/lawfully-present-immigrants/
- CFPB, Newcomer's Guides to Managing Money: https://www.consumerfinance.gov/about-us/blog/the-newcomers-guides-to-managing-money/
- HUD, Fair Housing Act overview: https://www.hud.gov/helping-americans/fair-housing-act-overview

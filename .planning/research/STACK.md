# Research: Stack

**Date:** 2026-05-09
**Project:** CivicBridge Simulator
**Research dimension:** Stack

## Recommendation

Use the existing OrgSim stack for v1. The codebase already has the right technical shape for a hackathon-grade product: scenario intake, persona simulation, streamed deliberation, risk extraction, and report presentation.

## Keep

- Next.js App Router frontend in `Frontend/`.
- FastAPI public API in `Backend/`.
- FastAPI simulation service in `Simulation/`.
- WebSocket event streaming from backend to frontend.
- Cascade/swarm simulation engines.
- YAML persona templates for fast domain iteration.
- Rule-based fallback paths for reliable demos.

## Simplify For Hackathon

- Treat TypeDB, Neo4j, NATS, and Temporal as optional during v1 unless a specific feature needs them.
- Keep the primary demo path runnable with frontend + API + simulation service.
- Avoid adding new frameworks before the first immigration-domain demo is working.

## Add

- Domain config for tracks, advisor personas, risk categories, and starter scenarios.
- A structured scenario intake model that captures status, goals, deadlines, location/state, family/dependents, work authorization, founder/company facts, and uncertainty.
- A report data shape for next steps, evidence gaps, caveats, and professional-review triggers.
- Official-source metadata fields, even if v1 uses curated static links rather than live retrieval.

## Source Strategy

Use official sources for legal/system facts:

- USCIS entrepreneur options, O-1, EB-1A, H-1B, International Entrepreneur Rule, and policy manual pages.
- IRS for taxes, ITIN/TIN, EIN, and filing dates.
- SSA for SSN eligibility and process.
- HealthCare.gov for health coverage eligibility.
- HUD/USAGov for housing rights and assistance.
- CFPB for newcomer banking and money-management materials.

## Avoid

- Adding a general web-search agent that freely summarizes immigration law without source constraints.
- Hardcoding time-sensitive immigration thresholds without source/date labels.
- Building a complex document vault before the scenario and report loop works.

## Sources

- USCIS, Options for Alien Entrepreneurs to Work in the United States: https://www.uscis.gov/working-in-the-united-states/options-for-alien-entrepreneurs-to-work-in-the-united-states
- USCIS, International Entrepreneur Rule: https://www.uscis.gov/working-in-the-united-states/international-entrepreneur-rule
- IRS, Individual tax filing: https://www.irs.gov/individual-tax-filing
- SSA, Immigration: https://www.ssa.gov/people/immigrants/
- HealthCare.gov, Lawfully present immigrants: https://www.healthcare.gov/immigrants/lawfully-present-immigrants/


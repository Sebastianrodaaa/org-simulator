# Research: Features

**Date:** 2026-05-09
**Project:** CivicBridge Simulator
**Research dimension:** Features

## Table Stakes

### Track Selection

- User can choose Founder Immigration or Learning to be American.
- User can start from guided demo scenarios for each track.
- User can paste a freeform situation when they do not know the right category.

### Structured Intake

- User can provide current status, goal, deadline, location/state, dependents, employer/company facts, and known constraints.
- Intake should ask for enough facts to make simulation useful without feeling like a legal form.
- Missing or uncertain answers should become explicit uncertainty, not silent assumptions.

### Advisor Simulation

- Founder track should include personas such as immigration attorney, founder mentor, employer/talent lead, evidence coach, tax/company navigator, and investor/operator advisor.
- First-1000-days track should include personas such as banking/credit navigator, healthcare navigator, housing navigator, tax/IRS navigator, school/work/community mentor, and scam/consumer-protection advisor.
- Simulation should produce a live activity stream and risk graph using existing UI mechanics.

### Risk/Blocker Extraction

- Replace "conflicts" with risk categories:
  - eligibility
  - evidence
  - timing
  - cost
  - compliance
  - work authorization
  - healthcare
  - housing
  - banking/credit
  - tax
  - language/access
  - professional review needed

### Action Report

- Report should include next actions, documents/evidence to gather, deadlines to verify, questions for a lawyer/advisor, and caveats.
- Report should distinguish "known", "unknown", and "must verify" facts.
- Report must include "not legal advice" framing.

## Differentiators

- Live simulation instead of a static checklist.
- Multiple advisor perspectives that expose second-order consequences.
- Combined founder + daily-life navigation in one tool.
- Risk graph that shows dependencies between immigration status, work, company, housing, banking, healthcare, and taxes.
- "Ask a professional" packet: concise questions and evidence list to bring to a lawyer, accountant, school, employer, clinic, bank, or housing office.

## Anti-Features

- Do not generate final legal determinations.
- Do not promise approval chances.
- Do not auto-complete immigration forms.
- Do not store sensitive documents in v1.
- Do not simulate government adjudication as if it were predictive truth.
- Do not treat all immigrants as having the same cultural or financial needs.

## Official Context

- USCIS describes founder-relevant pathways including entrepreneur options and International Entrepreneur Rule thresholds.
- HealthCare.gov distinguishes Marketplace eligibility for lawfully present immigrants and notes Medicaid/CHIP rules can depend on status, state, and waiting periods.
- IRS guidance emphasizes TIN/ITIN/EIN and federal filing requirements.
- SSA guidance notes SSN access generally depends on lawful presence and work authorization or valid nonwork reasons.
- HUD/USAGov/CFPB provide official navigation help for housing, discrimination, banking, and money management.

## Sources

- USCIS, Options for Alien Entrepreneurs: https://www.uscis.gov/working-in-the-united-states/options-for-alien-entrepreneurs-to-work-in-the-united-states
- USCIS, International Entrepreneur Rule: https://www.uscis.gov/working-in-the-united-states/international-entrepreneur-rule
- HealthCare.gov, Immigrant coverage: https://www.healthcare.gov/immigrants/lawfully-present-immigrants/
- IRS, ITIN: https://www.irs.gov/individuals/individual-taxpayer-identification-number
- CFPB, Newcomer's Guides to Managing Money: https://www.consumerfinance.gov/about-us/blog/the-newcomers-guides-to-managing-money/
- HUD, Fair Housing Act overview: https://www.hud.gov/helping-americans/fair-housing-act-overview


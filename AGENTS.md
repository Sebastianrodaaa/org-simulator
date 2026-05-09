# Agent Instructions

## Project

This repository is being repurposed from OrgSim into CivicBridge Simulator, a combined immigration and first-1000-days strategy simulator for the hackathon.

Read these planning files before major changes:

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/codebase/`
- `.planning/research/SUMMARY.md`

## Current Priority

Phase 1 is Product Shell and Intake. Preserve the existing simulation architecture while converting the visible product experience to an immigration-focused two-track tool.

## Engineering Rules

- Work with the existing FastAPI + Simulation + Next.js architecture.
- Do not remove user changes or unrelated dirty work.
- Keep demo reliability: fallback paths should still work without cloud keys.
- Avoid legal-outcome promises. Use planning, risk, uncertainty, and professional-review language.
- Prefer official sources for immigration, tax, healthcare, housing, banking, and government-system facts.
- Keep v1 focused on a coherent end-to-end demo.

## Useful Commands

- API: `cd Backend && uvicorn api.main:app --reload --port 8000`
- Simulation: `cd Simulation && uvicorn app:app --reload --port 8001`
- Frontend: `cd Frontend && npm run dev`
- Simulation tests: `pytest Simulation/tests -v`
- Frontend lint/build: `cd Frontend && npm run lint && npm run build`


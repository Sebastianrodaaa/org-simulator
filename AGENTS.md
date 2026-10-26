# Agent Instructions

## Project

This repository is OrgSim, the organizational decision rehearsal that won the IBM agent orchestration hackathon. Agents represent internal stakeholders (CFO, VP Sales, Operations, HR) and forecast cross-department conflicts before a C-suite decision is made. The CivicBridge immigration retarget is retired.

Read these planning files before major changes:

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/codebase/`
- `.planning/research/SUMMARY.md`

## Current Priority

Keep the visible product on the OrgSim department rehearsal. The primary demo is the CFO cutting Q4 marketing by 20% across Sales, Finance, Operations, and HR.

## Engineering Rules

- Work with the existing FastAPI + Simulation + Next.js architecture.
- Do not remove user changes or unrelated dirty work.
- Keep demo reliability: fallback paths should still work without cloud keys.
- Frame output as a conflict forecast for a decision that has not been made yet.
- Keep v1 focused on a coherent end-to-end demo.

## Useful Commands

- API: `cd Backend && uvicorn api.main:app --reload --port 8000`
- Simulation: `cd Simulation && uvicorn app:app --reload --port 8001`
- Frontend: `cd Frontend && npm run dev`
- Simulation tests: `pytest Simulation/tests -v`
- Frontend lint/build: `cd Frontend && npm run lint && npm run build`


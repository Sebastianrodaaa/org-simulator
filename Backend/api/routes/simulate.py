"""
POST /simulate  — trigger a simulation run
GET  /simulate/{run_id} — fetch run status
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Self

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from api import run_store
from api.simulation_snapshot import attach_snapshot_to_run
from api.services.live_simulation import live_simulation_enabled, run_live_streaming_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


def _append_stub_rehearsal_events(run_id: str) -> None:
    """
    Populate event_history for backend-only runs so attach_snapshot_to_run can build
    messages, risk-shaped conflicts, and the CivicBridge report on GET /simulate/{id}.
    """
    run = run_store.runs.get(run_id)
    if not run:
        return
    ts = datetime.now(tz=timezone.utc).isoformat()
    hist = run_store.event_history.setdefault(run_id, [])
    if any(ev.get("type") in {"agent_message", "conflict"} for ev in hist):
        return
    agents = [
        {"name": "CFO", "role": "CFO", "dept": "Finance"},
        {"name": "VP Sales", "role": "VP of Sales", "dept": "Sales"},
    ]
    hist.extend([
        {
            "type": "agent_message",
            "run_id": run_id,
            "timestamp": ts,
            "round": 1,
            "agent": agents[0],
            "message": (
                "The marketing line is discretionary. A 20% Q4 cut protects runway "
                "without touching headcount."
            ),
        },
        {
            "type": "agent_message",
            "run_id": run_id,
            "timestamp": ts,
            "round": 1,
            "agent": agents[1],
            "message": (
                "Late-stage deals depend on the campaigns this budget funds. "
                "Coverage falls under 3x if the cut lands on those programs."
            ),
        },
        {
            "type": "conflict",
            "run_id": run_id,
            "timestamp": ts,
            "round": 2,
            "agent": agents[1],
            "message": (
                "Conflict: Finance budget cut vs. pipeline coverage (8/10)."
            ),
        },
    ])

VALID_DEPARTMENTS = {"Sales", "Finance", "Operations", "HR", "Engineering", "Marketing"}


class SimulateRequest(BaseModel):
    decision: str
    departments: list[str] = Field(default_factory=list)
    track: Literal["founder", "first1000"] | None = None
    # Swarm = large pool of agents; each round only a subset speaks (real multi-agent debate).
    engine: Literal["cascade", "swarm"] = "swarm"
    rounds: int = Field(default=4, ge=1, le=40)
    swarm_size: Optional[int] = Field(default=24, ge=4, le=512)
    max_active_per_round: Optional[int] = Field(default=8, ge=2, le=128)

    @field_validator("decision")
    @classmethod
    def decision_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("decision must be a non-empty string")
        return v.strip()

    @model_validator(mode="after")
    def departments_valid_for_track(self) -> Self:
        if self.track is not None:
            return self
        if not self.departments:
            raise ValueError("departments must contain at least one entry when track is not set")
        invalid = set(self.departments) - VALID_DEPARTMENTS
        if invalid:
            raise ValueError(
                f"Unknown departments: {invalid}. Valid legacy names: {VALID_DEPARTMENTS}. "
                f"For CivicBridge, send track \"founder\" or \"first1000\" (departments may be empty)."
            )
        return self


class SimulationRun(BaseModel):
    run_id: str
    status: Literal["pending", "running", "complete", "failed"]
    decision: str
    departments: list[str]
    created_at: str
    recommendation: Optional[str] = None
    engine: Literal["cascade", "swarm"] = "cascade"
    messages: Optional[list[dict[str, Any]]] = None
    conflicts: Optional[list[dict[str, Any]]] = None
    report: Optional[dict[str, Any]] = None


async def _stub_run(run_id: str) -> None:
    """10-second stub used when no simulation service is configured."""
    await asyncio.sleep(2)
    if run_id in run_store.runs:
        run_store.runs[run_id]["status"] = "running"
    await asyncio.sleep(8)
    if run_id in run_store.runs:
        run_store.runs[run_id]["status"] = "complete"
        run_store.runs[run_id]["recommendation"] = (
            "Hold the cut on uncommitted brand spend. Re-forecast pipeline coverage "
            "and quota-team load before the number is locked."
        )
        _append_stub_rehearsal_events(run_id)
        attach_snapshot_to_run(run_id)


async def _run_streaming_background(run_id: str, req: SimulateRequest) -> None:
    """
    Drive the simulation service streaming pipeline, feeding events into the
    per-run asyncio.Queue so the WebSocket can relay them in real time.
    """
    queue = run_store.queues.get(run_id)
    if queue is None:
        logger.error("No queue for run %s — aborting streaming background", run_id)
        return

    try:
        run_store.runs[run_id]["status"] = "running"
        # Immediate heartbeat so clients see activity while personas generate.
        kickoff = {
            "type": "start",
            "run_id": run_id,
            "message": "Simulation initialized — preparing personas and round execution.",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        run_store.event_history.setdefault(run_id, []).append(kickoff)
        await queue.put(kickoff)
        logger.info("Kickoff event queued for run %s", run_id)
        rounds = min(15, req.rounds) if req.engine == "swarm" else min(40, req.rounds)
        rec = await run_live_streaming_pipeline(
            run_id=run_id,
            decision=req.decision,
            departments=req.departments,
            queue=queue,
            engine=req.engine,
            rounds=rounds,
            swarm_size=req.swarm_size,
            max_active_per_round=req.max_active_per_round,
            track=req.track,
        )
        attach_snapshot_to_run(run_id)
        run_store.runs[run_id]["status"] = "complete"
        if rec:
            run_store.runs[run_id]["recommendation"] = rec
    except Exception as exc:
        logger.exception("Streaming simulation failed for run %s", run_id)
        try:
            attach_snapshot_to_run(run_id)
        except Exception:
            logger.exception("attach_snapshot_to_run failed after streaming error for %s", run_id)
        run_store.runs[run_id]["status"] = "failed"
        run_store.runs[run_id]["recommendation"] = f"Simulation error: {exc}"
        # Push an error event so the WebSocket doesn't hang
        try:
            await queue.put({"type": "error", "run_id": run_id, "message": str(exc)})
        except Exception:
            pass
    finally:
        # Sentinel: tells the WebSocket reader to stop
        try:
            await queue.put(None)
        except Exception:
            pass
        # Keep the queue alive briefly for late-connecting WebSockets, then clean up
        await asyncio.sleep(60)
        run_store.queues.pop(run_id, None)
        # Keep recent history a bit longer so users can reconnect/view immediately.
        await asyncio.sleep(120)
        run_store.event_history.pop(run_id, None)


@router.post("", response_model=SimulationRun, status_code=202)
async def create_simulation(req: SimulateRequest, background_tasks: BackgroundTasks) -> SimulationRun:
    try:
        run_id = str(uuid.uuid4())
        use_live = live_simulation_enabled()

        run: dict = {
            "run_id": run_id,
            "status": "pending",
            "decision": req.decision,
            "departments": req.departments,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "recommendation": None,
            "engine": req.engine,
        }
        run_store.runs[run_id] = run
        run_store.event_history[run_id] = []

        if use_live:
            # Create the queue BEFORE scheduling the background task so the
            # WebSocket can connect and start waiting immediately.
            run_store.queues[run_id] = asyncio.Queue()
            logger.info(
                "Scheduling streaming simulation run %s (engine=%s)",
                run_id, req.engine,
            )
            background_tasks.add_task(_run_streaming_background, run_id, req)
        else:
            logger.warning(
                "SIMULATION_SERVICE_URL not set — stub mode for run %s", run_id
            )
            background_tasks.add_task(_stub_run, run_id)

        return SimulationRun(**{k: v for k, v in run.items()})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("create_simulation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create simulation run") from exc


@router.get("/{run_id}", response_model=SimulationRun)
async def get_simulation(run_id: str) -> SimulationRun:
    try:
        run = run_store.runs.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        return SimulationRun(**{k: v for k, v in run.items()})
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_simulation error for %s: %s", run_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch simulation run") from exc

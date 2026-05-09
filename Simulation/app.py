"""
OrgSim Simulation HTTP Service
===============================
FastAPI service running on port 8001.  Orchestrates persona generation,
the decision_cascade simulation loop, conflict extraction, and report
generation.  Publishes events to NATS JetStream when available.

Routes
------
POST /generate-personas   — build agent personas from seed reports + templates
POST /run-simulation      — run cascade or swarm engine for N rounds, emit NATS events
POST /extract-conflicts   — run conflict extractor over a message list
POST /generate-report     — compile DSPy executive report

Usage
-----
    cd Simulation && uvicorn app:app --port 8001 --reload
"""
from __future__ import annotations

import asyncio
import functools
import json
import logging
import os
import random
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config_loader import advisor_track_templates, department_templates, simulation_section
from org_persona_generator import build_all_personas, build_persona
from orgsim_engine.decision_cascade import DecisionCascadePlatform
from orgsim_engine.swarm_cascade import SwarmCascadePlatform
from swarm.persona_pool import build_swarm_personas, template_stem_from_swarm_username
from cascade.tracer import trace_cascade
from conflict.extractor import extract_conflicts
from report_agent import generate_report

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="OrgSim Simulation Service",
    version="0.1.0",
    description="Decision rehearsal simulation engine for OrgSim",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# NATS publisher (optional — graceful degradation when NATS is not running)
# ---------------------------------------------------------------------------

_nats_client: Any = None


async def _get_nats() -> Any:
    """Return a connected NATS client, or None if NATS is unavailable."""
    global _nats_client
    if _nats_client is not None:
        return _nats_client
    try:
        import nats  # type: ignore

        nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        _nats_client = await nats.connect(nats_url)
        logger.info("NATS connected: %s", nats_url)
        return _nats_client
    except Exception as exc:  # noqa: BLE001
        logger.warning("NATS unavailable (%s) — publishing disabled", exc)
        return None


async def _publish(subject: str, payload: dict[str, Any]) -> None:
    """Publish a JSON payload to a NATS subject; silently skips if unavailable."""
    nc = await _get_nats()
    if nc is None:
        return
    import json

    try:
        await nc.publish(subject, json.dumps(payload).encode())
    except Exception as exc:  # noqa: BLE001
        logger.warning("NATS publish failed on %s: %s", subject, exc)


def _ws_agent_envelope(run_id: str, msg: dict[str, Any]) -> dict[str, Any]:
    """Shape published on NATS so the dashboard WebSocket can render the feed."""
    role = str(msg.get("role", "Unknown"))
    dept = str(msg.get("department", "Unknown"))
    return {
        "type": "agent_message",
        "run_id": run_id,
        "timestamp": msg.get("timestamp"),
        "sequence": msg.get("msg_id"),
        "round": msg.get("round"),
        "agent": {"name": role, "role": role, "dept": dept},
        "message": str(msg.get("content", "")),
    }


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class GeneratePersonasRequest(BaseModel):
    decision: str = Field(..., description="The proposed business decision to simulate")
    departments: list[str] = Field(
        default_factory=list,
        description="Dept filter — empty list means all 4 default roles",
    )
    track: Literal["founder", "first1000"] | None = Field(
        default=None,
        description="CivicBridge track — when set, overrides department-based template selection",
    )


class GeneratePersonasResponse(BaseModel):
    run_id: str
    personas: list[dict[str, Any]]


class RunSimulationRequest(BaseModel):
    run_id: str
    personas: list[dict[str, Any]]
    decision: str
    rounds: int = Field(default=15, ge=1, le=40)
    engine: Literal["cascade", "swarm"] | None = Field(
        default=None,
        description="cascade = all personas speak each round; swarm = large pool, subset/round",
    )
    swarm_size: int | None = Field(default=None, ge=4, le=512)
    max_active_per_round: int | None = Field(default=None, ge=2, le=128)
    swarm_peer_recent: int | None = Field(default=None, ge=2, le=50)
    swarm_context_messages: int | None = Field(default=None, ge=20, le=500)


class MessageDict(BaseModel):
    msg_id: int
    round: int
    agent_id: str
    role: str
    department: str
    content: str
    action: str
    target_msg_id: int | None = None
    timestamp: str
    budget_authority: int
    reports_to_count: int


class RunSimulationResponse(BaseModel):
    run_id: str
    messages: list[dict[str, Any]]


class ExtractConflictsRequest(BaseModel):
    run_id: str
    messages: list[dict[str, Any]]


class ConflictDict(BaseModel):
    conflict_id: str
    dept_a: str
    dept_b: str
    conflict_type: str  # "resource" | "priority" | "timeline" | "budget"
    severity: str       # "low" | "medium" | "high"
    description: str
    round_detected: int
    agent_a_message: str
    agent_b_message: str


class ExtractConflictsResponse(BaseModel):
    run_id: str
    conflicts: list[dict[str, Any]]


class GenerateReportRequest(BaseModel):
    run_id: str
    messages: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]


class ReportDict(BaseModel):
    executive_summary: str
    key_risks: list[str]
    recommended_actions: list[str]
    confidence_score: float


class GenerateReportResponse(BaseModel):
    run_id: str
    report: dict[str, Any]


# ---------------------------------------------------------------------------
# Agent ID → template mapping
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post("/generate-personas", response_model=GeneratePersonasResponse)
async def generate_personas(req: GeneratePersonasRequest) -> GeneratePersonasResponse:
    """
    Load seed reports for each department and build agent persona dicts.
    If ``track`` is set (CivicBridge), advisor templates for that track are used
    and ``departments`` is ignored. If ``track`` is unset and ``departments`` is
    empty, all 4 default org roles are generated.
    """
    run_id = str(uuid.uuid4())
    logger.info(
        "[%s] generate-personas: decision=%r depts=%s track=%s",
        run_id,
        req.decision,
        req.departments,
        req.track,
    )

    dept_map = department_templates()
    loop = asyncio.get_event_loop()
    if req.track is not None:
        agent_ids = advisor_track_templates(req.track)
        if not agent_ids:
            logger.warning("[%s] advisor_track_templates(%r) empty — falling back", run_id, req.track)
        else:
            personas = await loop.run_in_executor(
                None,
                functools.partial(
                    lambda ids, dec: [build_persona(a, dec) for a in ids],
                    agent_ids,
                    req.decision,
                ),
            )
            logger.info("[%s] Generated %d personas (track=%s)", run_id, len(personas), req.track)
            return GeneratePersonasResponse(run_id=run_id, personas=personas)
    if req.departments:
        agent_ids: list[str] = []
        for dept in req.departments:
            aid = dept_map.get(dept)
            if aid and aid not in agent_ids:
                agent_ids.append(aid)
        # Run blocking DSPy/Ollama calls in a thread so the event loop stays free
        personas = await loop.run_in_executor(
            None,
            functools.partial(
                lambda ids, dec: [build_persona(a, dec) for a in ids],
                agent_ids,
                req.decision,
            ),
        )
    else:
        personas = await loop.run_in_executor(
            None, functools.partial(build_all_personas, scenario=req.decision)
        )

    logger.info("[%s] Generated %d personas", run_id, len(personas))
    return GeneratePersonasResponse(run_id=run_id, personas=personas)


@app.post("/run-simulation", response_model=RunSimulationResponse)
async def run_simulation(req: RunSimulationRequest) -> RunSimulationResponse:
    """
    Run the decision_cascade simulation for the requested number of rounds.

    The cascade impact map is computed first (TypeDB traversal) and injected
    into each agent's context so they are aware of cross-dept dependencies.

    Each agent message is published to NATS: orgsim.simulation.{run_id}.agent
    """
    run_id = req.run_id
    sim_cfg = simulation_section()
    engine = (req.engine or sim_cfg.get("engine") or "cascade").lower()
    if engine not in ("cascade", "swarm"):
        engine = "cascade"

    swarm_n = int(req.swarm_size or sim_cfg.get("swarm_size") or 64)
    max_act = int(req.max_active_per_round or sim_cfg.get("max_active_per_round") or 14)
    peer_r = int(req.swarm_peer_recent or sim_cfg.get("swarm_peer_recent") or 10)
    ctx_max = int(req.swarm_context_messages or sim_cfg.get("swarm_context_messages") or 120)

    if engine == "swarm":
        seen_ids: list[str] = []
        seen_set: set[str] = set()
        for p in req.personas:
            raw = str(p.get("username") or p.get("agent_id") or "").strip()
            stem = template_stem_from_swarm_username(raw)
            if stem and stem not in seen_set:
                seen_set.add(stem)
                seen_ids.append(stem)
        rng_seed = hash(run_id) & 0xFFFF_FFFF
        if seen_ids:
            personas = build_swarm_personas(
                req.decision,
                [],
                swarm_n,
                rng=random.Random(rng_seed),
                template_ids=seen_ids,
            )
        else:
            departments = sorted({str(p.get("department", "Sales")) for p in req.personas})
            personas = build_swarm_personas(
                req.decision,
                list(departments),
                swarm_n,
                rng=random.Random(rng_seed),
            )
        platform = SwarmCascadePlatform(
            req.decision,
            max_active_per_round=max_act,
            peer_recent_count=peer_r,
            context_thread_max=ctx_max,
            rng=random.Random(rng_seed),
        )
    else:
        personas = req.personas
        platform = DecisionCascadePlatform(req.decision)

    logger.info(
        "[%s] run-simulation: engine=%s rounds=%d agents=%d",
        run_id, engine, req.rounds, len(personas),
    )

    # ------------------------------------------------------------------
    # 1. Build cascade context (TypeDB traversal — graceful fallback)
    # ------------------------------------------------------------------
    primary_depts = list({p["department"] for p in personas})
    try:
        cascade_map = trace_cascade(req.decision, primary_depts)
        logger.info("[%s] Cascade map: %d primary + %d secondary impacts",
                    run_id,
                    len(cascade_map.get("primary_impact", [])),
                    len(cascade_map.get("secondary_impact", [])))
    except Exception as exc:  # noqa: BLE001
        logger.warning("[%s] Cascade tracer failed (%s) — using empty map", run_id, exc)
        cascade_map = {"decision": req.decision, "primary_impact": [], "secondary_impact": []}

    # ------------------------------------------------------------------
    # 2. Run simulation
    # ------------------------------------------------------------------
    platform.inject_scenario()

    capped_rounds = min(req.rounds, 40)
    loop = asyncio.get_event_loop()
    for round_num in range(1, capped_rounds + 1):
        round_msgs = await loop.run_in_executor(
            None, platform.run_round, round_num, personas
        )
        for msg in round_msgs:
            await _publish(
                subject=f"orgsim.simulation.{run_id}.agent",
                payload=_ws_agent_envelope(run_id, msg),
            )

    all_messages = platform.get_thread()
    logger.info("[%s] Simulation complete: %d messages across %d rounds",
                run_id, len(all_messages), capped_rounds)

    return RunSimulationResponse(run_id=run_id, messages=all_messages)


@app.post("/stream-simulation")
async def stream_simulation(req: RunSimulationRequest) -> StreamingResponse:
    """
    Run the simulation and stream NDJSON events line-by-line as each round
    completes.  The backend queue stream reads this without needing NATS.

    Each line is a JSON object:
      {"type": "agent_message", ...}  — one per agent message
      {"type": "conflict", ...}       — one per detected conflict
      {"type": "complete", ...}       — final event
    """
    run_id = req.run_id
    sim_cfg = simulation_section()
    engine = (req.engine or sim_cfg.get("engine") or "cascade").lower()
    if engine not in ("cascade", "swarm"):
        engine = "cascade"

    swarm_n = int(req.swarm_size or sim_cfg.get("swarm_size") or 64)
    max_act = int(req.max_active_per_round or sim_cfg.get("max_active_per_round") or 20)
    peer_r = int(req.swarm_peer_recent or sim_cfg.get("swarm_peer_recent") or 10)
    ctx_max = int(req.swarm_context_messages or sim_cfg.get("swarm_context_messages") or 120)

    if engine == "swarm":
        seen_ids: list[str] = []
        seen_set: set[str] = set()
        for p in req.personas:
            raw = str(p.get("username") or p.get("agent_id") or "").strip()
            stem = template_stem_from_swarm_username(raw)
            if stem and stem not in seen_set:
                seen_set.add(stem)
                seen_ids.append(stem)
        rng_seed = hash(run_id) & 0xFFFF_FFFF
        if seen_ids:
            personas = build_swarm_personas(
                req.decision,
                [],
                swarm_n,
                rng=random.Random(rng_seed),
                template_ids=seen_ids,
            )
        else:
            departments = sorted({str(p.get("department", "Sales")) for p in req.personas})
            personas = build_swarm_personas(
                req.decision,
                list(departments),
                swarm_n,
                rng=random.Random(rng_seed),
            )
        platform: DecisionCascadePlatform | SwarmCascadePlatform = SwarmCascadePlatform(
            req.decision,
            max_active_per_round=max_act,
            peer_recent_count=peer_r,
            context_thread_max=ctx_max,
            rng=random.Random(rng_seed),
        )
    else:
        personas = req.personas
        platform = DecisionCascadePlatform(req.decision)

    primary_depts = list({p["department"] for p in personas})
    try:
        cascade_map = trace_cascade(req.decision, primary_depts)
    except Exception as exc:
        logger.warning("[%s] Cascade tracer failed (%s) — using empty map", run_id, exc)
        cascade_map = {"decision": req.decision, "primary_impact": [], "secondary_impact": []}

    platform.inject_scenario()
    capped_rounds = min(req.rounds, 40)
    loop = asyncio.get_event_loop()

    async def _generate() -> AsyncIterator[str]:
        # Run each round in a thread-pool executor so the async generator
        # can actually yield between rounds without blocking the event loop.
        for round_num in range(1, capped_rounds + 1):
            round_msgs: list[dict[str, Any]] = await loop.run_in_executor(
                None, platform.run_round, round_num, personas
            )
            for msg in round_msgs:
                yield json.dumps(_ws_agent_envelope(run_id, msg)) + "\n"
                # Pace output so the frontend visualization can render between
                # messages. With rule-based fallback (Ollama OOM / unavailable)
                # rounds complete in milliseconds; without this delay the entire
                # simulation flushes as a single burst before the UI can animate.
                await asyncio.sleep(0.8)
            await asyncio.sleep(0.5)  # brief gap between rounds

        # After all rounds: extract conflicts and emit conflict events
        all_messages = platform.get_thread()
        try:
            conflicts = extract_conflicts(all_messages)
        except Exception as exc:
            logger.warning("[%s] Conflict extraction failed (%s)", run_id, exc)
            conflicts = []

        ts = datetime.now(tz=timezone.utc).isoformat()
        for conflict in conflicts:
            yield json.dumps({
                "type": "conflict",
                "run_id": run_id,
                "timestamp": ts,
                "data": {**conflict, "run_id": run_id},
                "agent": {
                    "name": "Conflict Detector",
                    "role": "Cross-dept",
                    "dept": str(conflict.get("dept_a", "Unknown")),
                },
                "message": str(conflict.get("description", "")),
            }) + "\n"

        yield json.dumps({
            "type": "complete",
            "run_id": run_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "summary": {
                "total_messages": len(all_messages),
                "conflicts_detected": len(conflicts),
                "recommendation": (
                    "Review detected cross-department conflicts before proceeding."
                    if conflicts
                    else "No hard conflicts surfaced in this rehearsal window."
                ),
            },
        }) + "\n"

    return StreamingResponse(_generate(), media_type="application/x-ndjson")


@app.post("/extract-conflicts", response_model=ExtractConflictsResponse)
async def extract_conflicts_route(req: ExtractConflictsRequest) -> ExtractConflictsResponse:
    """
    Identify conflicts in the simulation message list.
    Each conflict is published to NATS: orgsim.simulation.{run_id}.conflict
    """
    run_id = req.run_id
    logger.info("[%s] extract-conflicts: %d messages", run_id, len(req.messages))

    conflicts = extract_conflicts(req.messages)
    logger.info("[%s] Detected %d conflicts", run_id, len(conflicts))

    ts = datetime.now(tz=timezone.utc).isoformat()
    for conflict in conflicts:
        await _publish(
            subject=f"orgsim.simulation.{run_id}.conflict",
            payload={
                "type": "conflict",
                "run_id": run_id,
                "timestamp": ts,
                "data": {**conflict, "run_id": run_id},
                "agent": {
                    "name": "Conflict",
                    "role": "Cross-dept",
                    "dept": str(conflict.get("dept_a", "Unknown")),
                },
                "message": str(conflict.get("description", "")),
            },
        )

    return ExtractConflictsResponse(run_id=run_id, conflicts=conflicts)


@app.post("/generate-report", response_model=GenerateReportResponse)
async def generate_report_route(req: GenerateReportRequest) -> GenerateReportResponse:
    """
    Compile a DSPy executive report from messages and conflicts.
    """
    run_id = req.run_id
    logger.info(
        "[%s] generate-report: %d messages, %d conflicts",
        run_id, len(req.messages), len(req.conflicts),
    )

    # Rebuild cascade map from message metadata (best-effort)
    primary_depts = list({m.get("department", "") for m in req.messages if m.get("agent_id") != "system"})
    try:
        # Infer decision from system message
        decision = req.messages[0]["content"] if req.messages else "unknown decision"
        cascade_map = trace_cascade(decision, primary_depts)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[%s] Cascade tracer in report failed (%s)", run_id, exc)
        cascade_map = {"decision": "unknown", "primary_impact": [], "secondary_impact": []}

    report = generate_report(
        run_id=run_id,
        messages=req.messages,
        conflicts=req.conflicts,
        cascade_map=cascade_map,
    )

    return GenerateReportResponse(run_id=run_id, report=report)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orgsim-simulation"}

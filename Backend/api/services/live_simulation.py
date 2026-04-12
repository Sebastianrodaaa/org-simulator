"""
Drive the OrgSim simulation service (port 8001) via its streaming endpoint.

Events arrive line-by-line (NDJSON) and are placed into an asyncio.Queue
so the WebSocket handler can relay them to the browser in real time —
no NATS required.

If ``SIMULATION_SERVICE_URL`` is unset, a probe to ``http://127.0.0.1:8001/health``
is used so local dev works without extra env wiring.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_LOCAL = "http://127.0.0.1:8001"


def _health_ok_sync(base: str) -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{base.rstrip('/')}/health")
            return r.status_code == 200
    except Exception:
        return False


def resolve_simulation_service_url() -> str | None:
    """
    Return the base URL for the simulation HTTP service, or None if unavailable.

    Order: explicit ``SIMULATION_SERVICE_URL`` (must pass health), else localhost:8001.
    """
    explicit = os.getenv("SIMULATION_SERVICE_URL", "").strip()
    if explicit:
        base = explicit.rstrip("/")
        if _health_ok_sync(base):
            return base
        logger.warning("SIMULATION_SERVICE_URL=%s is not healthy — probe failed", base)
        return None
    base = _DEFAULT_LOCAL
    if _health_ok_sync(base):
        logger.info("Using default simulation service at %s", base)
        return base
    return None


def live_simulation_enabled() -> bool:
    return resolve_simulation_service_url() is not None


async def run_live_streaming_pipeline(
    run_id: str,
    decision: str,
    departments: list[str],
    queue: asyncio.Queue,
    *,
    engine: str = "cascade",
    rounds: int = 15,
    swarm_size: int | None = None,
    max_active_per_round: int | None = None,
) -> str | None:
    """
    1. POST /generate-personas  → get persona list
    2. POST /stream-simulation  → read NDJSON stream, put each event in queue

    The queue sentinel (None) is appended by the caller (_run_streaming_background)
    after this coroutine returns so cleanup is always guaranteed.

    Returns the ``recommendation`` string from the terminal ``complete`` event, if any.
    """
    base_url = resolve_simulation_service_url()
    if base_url is None:
        raise RuntimeError(
            "Simulation engine is not reachable. Start it with: "
            "cd Simulation && uvicorn app:app --port 8001"
        )
    base = base_url.rstrip("/")
    # Long timeout: persona gen + many LLM rounds
    timeout = httpx.Timeout(360.0, connect=15.0)
    recommendation: str | None = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        # ── 1. Generate personas ────────────────────────────────────────────
        logger.info("[%s] Calling generate-personas…", run_id)
        gp = await client.post(
            f"{base}/generate-personas",
            json={"decision": decision, "departments": departments},
        )
        gp.raise_for_status()
        personas: list[dict[str, Any]] = gp.json()["personas"]
        logger.info("[%s] %d personas generated", run_id, len(personas))

        # Emit a synthetic start event so the WebSocket client knows we're live
        await queue.put({
            "type": "start",
            "run_id": run_id,
            "agent_count": len(personas),
            "message": f"Simulation starting — {len(personas)} personas generated",
        })

        # ── 2. Stream simulation rounds ─────────────────────────────────────
        body: dict[str, Any] = {
            "run_id": run_id,
            "personas": personas,
            "decision": decision,
            "rounds": max(1, min(40, rounds)),
            "engine": engine if engine in ("cascade", "swarm") else "cascade",
        }
        if swarm_size is not None:
            body["swarm_size"] = swarm_size
        if max_active_per_round is not None:
            body["max_active_per_round"] = max_active_per_round

        logger.info("[%s] Opening stream-simulation (engine=%s, rounds=%d)…", run_id, engine, rounds)
        async with client.stream("POST", f"{base}/stream-simulation", json=body) as resp:
            resp.raise_for_status()
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    await queue.put(event)
                    etype = event.get("type", "?")
                    if etype == "complete":
                        summary = event.get("summary") or {}
                        if isinstance(summary, dict):
                            rec = summary.get("recommendation")
                            if isinstance(rec, str) and rec.strip():
                                recommendation = rec.strip()
                    logger.debug("[%s] Queued event: %s", run_id, etype)
                except json.JSONDecodeError as exc:
                    logger.warning("[%s] Skipping malformed NDJSON line (%s): %.80s", run_id, exc, line)

    logger.info("[%s] Streaming pipeline complete", run_id)
    return recommendation

"""
WebSocket /ws/simulation/{run_id}

Priority order for event delivery:
  1. In-memory asyncio.Queue (live streaming via simulation service — no NATS needed)
  2. NATS JetStream relay (when NATS is running and queue not present)
  3. Mock stream (fallback when neither is available)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api import run_store
from api.nats_client import get_jetstream, get_subject

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Mock fallback data ────────────────────────────────────────────────────────

_MOCK_AGENTS = [
    {"name": "CFO",         "role": "Chief Financial Officer",  "dept": "Finance"},
    {"name": "VP Sales",    "role": "VP of Sales",              "dept": "Sales"},
    {"name": "Ops Lead",    "role": "Operations Lead",          "dept": "Operations"},
    {"name": "HR Director", "role": "HR Director",              "dept": "HR"},
]

_MOCK_EVENTS = [
    ("agent_message", "CFO",         "Reviewing the financial impact of this decision on Q4 targets."),
    ("agent_message", "VP Sales",    "Pipeline coverage drops if marketing spend is cut — deals are at risk."),
    ("agent_message", "Ops Lead",    "Ops capacity is at 94%; any headcount freeze compounds the problem."),
    ("agent_message", "HR Director", "Engagement scores may decline if budget signals instability."),
    ("agent_message", "CFO",         "The 20% cut translates to a $56k reduction in campaign budget."),
    ("agent_message", "VP Sales",    "Three enterprise deals close in Q4 — marketing support is critical."),
    ("agent_message", "Ops Lead",    "Infra costs are fixed; the cut must come from headcount or campaigns."),
    ("agent_message", "HR Director", "Top performer flight risk is already elevated in Sales."),
    ("conflict",      "VP Sales",    "Conflict: Sales pipeline depends on Marketing spend (strength 8/10)."),
    ("conflict",      "Ops Lead",    "Conflict: Engineering capacity limits Sales feature delivery (strength 9/10)."),
    ("agent_message", "CFO",         "Finance confirms runway stays at 18 months — this cut is discretionary."),
    ("agent_message", "VP Sales",    "Estimated 12% velocity drop without campaign spend. $340k pipeline at risk."),
    ("agent_message", "HR Director", "HR recommends a 90-day freeze review rather than immediate cut."),
    ("agent_message", "Ops Lead",    "We should model the revenue delta before committing to this reduction."),
    ("agent_message", "CFO",         "Consensus forming: defer to Q1 and run a partial reduction pilot instead."),
]


def _ts() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _mock_websocket_allowed() -> bool:
    return os.getenv("ORGSIM_ALLOW_MOCK_WEBSOCKET", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


async def _honest_no_stream(websocket: WebSocket, run_id: str) -> None:
    """Tell the client no live feed exists (avoid scripted fake transcripts)."""
    await websocket.send_json({
        "type": "error",
        "run_id": run_id,
        "timestamp": _ts(),
        "message": (
            "No live simulation stream is attached to this run. "
            "Start the Simulation service on port 8001 before creating a run, "
            "or connect the WebSocket immediately after starting a simulation."
        ),
    })
    await websocket.send_json({
        "type": "complete",
        "run_id": run_id,
        "timestamp": _ts(),
        "summary": {
            "total_messages": 0,
            "conflicts_detected": 0,
            "recommendation": (
                "No live data for this session — enable the simulation engine on port 8001."
            ),
        },
    })


async def _mock_stream(websocket: WebSocket, run_id: str) -> None:
    """Send mock events when no live simulation is available."""
    for i, (event_type, agent_name, message) in enumerate(_MOCK_EVENTS):
        agent = next((a for a in _MOCK_AGENTS if a["name"] == agent_name), _MOCK_AGENTS[0])
        event: dict[str, Any] = {
            "type": event_type,
            "run_id": run_id,
            "timestamp": _ts(),
            "agent": agent,
            "message": message,
            "sequence": i + 1,
        }
        await websocket.send_json(event)
        await asyncio.sleep(0.5)

    await websocket.send_json({
        "type": "complete",
        "run_id": run_id,
        "timestamp": _ts(),
        "summary": {
            "total_messages": len(_MOCK_EVENTS),
            "conflicts_detected": 2,
            "recommendation": "Defer Q4 cut; run partial pilot in Q1 with 30-day review gate.",
        },
    })
    logger.info("Mock stream complete for run %s", run_id)


async def _queue_stream(websocket: WebSocket, run_id: str, queue: asyncio.Queue) -> None:
    """
    Relay events from the in-memory queue to the WebSocket.

    The background task places events as dicts and a None sentinel when done.
    Waits up to 180 s for the first event (covers slow persona-gen + round 1).
    """
    logger.info("Queue stream started for run %s", run_id)
    first = True
    while True:
        # First event: allow up to 240s (persona gen ~42s + round 1 LLM time).
        # Subsequent events: allow up to 300s per round — qwen2.5:14b can take
        # 60-120s per agent call; with 4 agents in parallel a single round may
        # exceed 60s. 300s matches the simulation's own per-round executor timeout
        # so the stream never dies before the round actually times out.
        timeout = 240.0 if first else 300.0
        try:
            event = await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Queue stream timeout for run %s — closing", run_id)
            break

        first = False

        if event is None:
            # Sentinel — background task is done; close cleanly
            logger.info("Queue sentinel received for run %s", run_id)
            break

        await websocket.send_json(event)

        etype = event.get("type", "")
        if etype in ("complete", "error"):
            break

    logger.info("Queue stream finished for run %s", run_id)


async def _nats_stream(websocket: WebSocket, run_id: str) -> None:
    """Relay NATS JetStream messages to the WebSocket."""
    js = await get_jetstream()
    if js is None:
        logger.warning("JetStream not available for run %s — stream fallback", run_id)
        if _mock_websocket_allowed():
            await _mock_stream(websocket, run_id)
        else:
            await _honest_no_stream(websocket, run_id)
        return

    subject = get_subject(run_id, "*")
    sub = await js.subscribe(subject, deliver_policy="all")
    logger.info("NATS subscription opened: %s", subject)
    received_any = False
    unsubscribed = False

    async def _unsub() -> None:
        nonlocal unsubscribed
        if not unsubscribed:
            unsubscribed = True
            try:
                await sub.unsubscribe()
            except Exception:
                pass

    try:
        while True:
            timeout = 30.0 if received_any else 4.0
            try:
                msg = await sub.next_msg(timeout=timeout)
                await msg.ack()
                received_any = True
                try:
                    payload = json.loads(msg.data.decode())
                except json.JSONDecodeError:
                    payload = {"raw": msg.data.decode()}
                await websocket.send_json(payload)
                if payload.get("type") == "complete":
                    await asyncio.sleep(0.5)
                    break
            except Exception as exc:
                is_timeout = (
                    "timeout" in type(exc).__name__.lower()
                    or isinstance(exc, (asyncio.TimeoutError, TimeoutError))
                )
                if is_timeout and not received_any:
                    logger.warning("No NATS events after %.0fs for run %s — stream fallback", timeout, run_id)
                    await _unsub()
                    if _mock_websocket_allowed():
                        await _mock_stream(websocket, run_id)
                    else:
                        await _honest_no_stream(websocket, run_id)
                    return
                if is_timeout:
                    logger.warning("NATS per-message timeout on run %s", run_id)
                    break
                logger.warning("NATS error on run %s (%s) — stream fallback", run_id, exc)
                await _unsub()
                if _mock_websocket_allowed():
                    await _mock_stream(websocket, run_id)
                else:
                    await _honest_no_stream(websocket, run_id)
                return
    finally:
        await _unsub()
        logger.info("NATS subscription closed for run %s", run_id)


@router.websocket("/ws/simulation/{run_id}")
async def simulation_ws(websocket: WebSocket, run_id: str) -> None:
    await websocket.accept()
    logger.info("WebSocket connected: run_id=%s", run_id)

    try:
        # Priority 1: live streaming queue (no NATS needed)
        queue = run_store.queues.get(run_id)
        if queue is not None:
            logger.info("Using queue stream for run %s", run_id)
            await _queue_stream(websocket, run_id, queue)
            return

        # Priority 2: NATS relay
        js = await get_jetstream()
        if js is not None:
            await _nats_stream(websocket, run_id)
            return

        # Priority 3: optional scripted mock (tests only — off by default)
        if _mock_websocket_allowed():
            logger.info("No queue or NATS — mock stream for run %s", run_id)
            await _mock_stream(websocket, run_id)
        else:
            logger.warning("No queue or NATS — honest no-stream for run %s", run_id)
            await _honest_no_stream(websocket, run_id)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: run_id=%s", run_id)
    except Exception as exc:
        logger.error("WebSocket error for run %s: %s", run_id, exc, exc_info=True)
        try:
            await websocket.send_json({"type": "error", "run_id": run_id, "message": str(exc)})
        except Exception:
            pass
    finally:
        logger.info("WebSocket closed: run_id=%s", run_id)

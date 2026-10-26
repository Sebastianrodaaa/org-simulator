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
from api.simulation_snapshot import attach_snapshot_to_run

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Mock fallback data ────────────────────────────────────────────────────────

# OrgSim mock: department stakeholders debating a budget cut.
_MOCK_AGENTS = [
    {"name": "CFO", "role": "CFO", "dept": "Finance"},
    {"name": "VP Sales", "role": "VP of Sales", "dept": "Sales"},
    {"name": "Ops Lead", "role": "Operations Lead", "dept": "Operations"},
    {"name": "HR Director", "role": "HR Director", "dept": "HR"},
]

_MOCK_EVENTS = [
    ("agent_message", "CFO", "Q4 marketing is the discretionary line. A 20% cut protects runway without a hiring freeze."),
    ("agent_message", "VP Sales", "Three late-stage deals depend on the campaigns this budget funds. Coverage drops under 3x."),
    ("agent_message", "Ops Lead", "Delivery capacity does not shrink with the marketing line. Close dates will slip into next quarter."),
    ("agent_message", "HR Director", "Quota pressure plus a public cut reads as instability. Attrition risk is on the AE team."),
    ("agent_message", "CFO", "I will take the pipeline note. I will not hold the full budget after the cut is the decision."),
    ("agent_message", "VP Sales", "Then move the cut to brand spend and keep the late-stage programs. Otherwise Q4 misses."),
    ("agent_message", "Ops Lead", "Flag handoff dates before Finance locks the number. We are already at capacity."),
    ("agent_message", "HR Director", "Do not pair this with a backfill freeze on the same team carrying the pipeline."),
    ("conflict", "VP Sales", "Conflict: marketing cut vs. Q4 pipeline coverage (strength 8/10)."),
    ("conflict", "HR Director", "Conflict: cost cut vs. quota-team attrition (strength 7/10)."),
    ("agent_message", "CFO", "Compromise: cut 20% of brand, hold the programs tied to named late-stage deals."),
    ("agent_message", "VP Sales", "That keeps the three deals. I can live with the brand cut if coverage stays above 3x."),
    ("agent_message", "Ops Lead", "Accepted, if close dates are reforecast before the board pack."),
    ("agent_message", "HR Director", "Accepted, if we do not freeze AE backfill in the same quarter."),
    ("agent_message", "CFO", "Consensus: 20% brand cut, named-deal programs held, no AE freeze, reforecast the handoffs."),
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
    try:
        attach_snapshot_to_run(run_id)
    except Exception:
        logger.exception("attach_snapshot_to_run failed after honest no-stream for %s", run_id)


async def _mock_stream(websocket: WebSocket, run_id: str) -> None:
    """Send mock events when no live simulation is available."""
    hist = run_store.event_history.setdefault(run_id, [])
    for i, (event_type, agent_name, message) in enumerate(_MOCK_EVENTS):
        agent = next((a for a in _MOCK_AGENTS if a["name"] == agent_name), _MOCK_AGENTS[0])
        event: dict[str, Any] = {
            "type": event_type,
            "run_id": run_id,
            "timestamp": _ts(),
            "agent": agent,
            "message": message,
            "sequence": i + 1,
            "round": (i // 4) + 1,
        }
        hist.append(dict(event))
        await websocket.send_json(event)
        await asyncio.sleep(0.5)

    await websocket.send_json({
        "type": "complete",
        "run_id": run_id,
        "timestamp": _ts(),
        "summary": {
            "total_messages": len(_MOCK_EVENTS),
            "conflicts_detected": 2,
            "recommendation": "Rehearse evidence sprint + payroll timing with explicit dates; schedule professional review checkpoints.",
        },
    })
    try:
        attach_snapshot_to_run(run_id)
    except Exception:
        logger.exception("attach_snapshot_to_run failed after mock stream for %s", run_id)
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


async def _history_stream(websocket: WebSocket, run_id: str) -> bool:
    """
    Replay buffered events for runs that completed before WS attached/re-attached.
    Returns True if history was sent.
    """
    history = run_store.event_history.get(run_id) or []
    if not history:
        return False
    logger.info("Replaying %d buffered events for run %s", len(history), run_id)
    for event in history:
        await websocket.send_json(event)
    return True


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

        # Priority 1b: replay completed/backlogged events if available
        if await _history_stream(websocket, run_id):
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

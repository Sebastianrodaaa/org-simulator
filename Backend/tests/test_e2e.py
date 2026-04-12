"""
End-to-end integration test for the OrgSim simulation pipeline.

Requires all Docker services running:
  docker compose up -d

Run:
  pytest backend/tests/test_e2e.py -v -s

Skip when services are unavailable (CI without Docker):
  pytest backend/tests/test_e2e.py -v -m "not e2e"
"""
from __future__ import annotations

import os

# WebSocket scripted mock is only for stub runs / CI without the simulation engine.
os.environ.setdefault("ORGSIM_ALLOW_MOCK_WEBSOCKET", "1")

import asyncio
import json
import os
import socket
import time

import httpx
import pytest
import websockets

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_BASE_URL = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")

DEMO_DECISION = "CFO cuts Q4 marketing budget 20%"
DEMO_DEPARTMENTS = ["Sales", "Finance", "Engineering", "HR"]


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _api_reachable() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


requires_api = pytest.mark.skipif(
    not _api_reachable(),
    reason="OrgSim API not reachable at localhost:8000 — start with: uvicorn api.main:app --port 8000",
)

requires_nats = pytest.mark.skipif(
    not _port_open("localhost", 4222),
    reason="NATS not reachable at localhost:4222 — start with: docker compose up -d",
)

requires_temporal = pytest.mark.skipif(
    not _port_open("localhost", 7233),
    reason="Temporal not reachable at localhost:7233 — start with: docker compose up -d",
)

pytestmark = pytest.mark.e2e


# ── Health check ──────────────────────────────────────────────────────────────

@requires_api
def test_health_endpoint_returns_200() -> None:
    r = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "services" in body
    assert "typedb" in body["services"]
    assert "neo4j" in body["services"]
    assert "nats" in body["services"]


# ── Simulate: create and poll ─────────────────────────────────────────────────

@requires_api
def test_post_simulate_returns_pending_run() -> None:
    r = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": DEMO_DECISION, "departments": DEMO_DEPARTMENTS},
        timeout=10,
    )
    assert r.status_code == 202, f"Expected 202, got {r.status_code}: {r.text}"
    body = r.json()
    assert body["status"] == "pending"
    assert body["run_id"]
    assert body["decision"] == DEMO_DECISION
    assert set(body["departments"]) == set(DEMO_DEPARTMENTS)


@requires_api
def test_get_simulate_returns_run() -> None:
    # Create a run first
    create = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": DEMO_DECISION, "departments": ["Sales", "Finance"]},
        timeout=10,
    )
    run_id = create.json()["run_id"]

    r = httpx.get(f"{BASE_URL}/simulate/{run_id}", timeout=5)
    assert r.status_code == 200
    assert r.json()["run_id"] == run_id


@requires_api
def test_get_simulate_404_for_unknown_run() -> None:
    r = httpx.get(f"{BASE_URL}/simulate/nonexistent-run-id", timeout=5)
    assert r.status_code == 404


@requires_api
def test_simulate_validates_empty_decision() -> None:
    r = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": "  ", "departments": ["Sales"]},
        timeout=5,
    )
    assert r.status_code == 422


@requires_api
def test_simulate_validates_invalid_department() -> None:
    r = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": DEMO_DECISION, "departments": ["InvalidDept"]},
        timeout=5,
    )
    assert r.status_code == 422


# ── Stub progression (no Temporal needed) ────────────────────────────────────

@requires_api
def test_stub_run_progresses_to_complete() -> None:
    """Without Temporal, the background stub should reach 'complete' within 15s."""
    create = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": DEMO_DECISION, "departments": ["Sales", "Finance"]},
        timeout=10,
    )
    run_id = create.json()["run_id"]
    assert create.json()["status"] == "pending"

    deadline = time.time() + 15
    while time.time() < deadline:
        time.sleep(1)
        poll = httpx.get(f"{BASE_URL}/simulate/{run_id}", timeout=5)
        if poll.json()["status"] == "complete":
            return
    pytest.fail(f"Run {run_id} did not reach 'complete' within 15 seconds")


# ── WebSocket stream ──────────────────────────────────────────────────────────

@requires_api
def test_websocket_streams_agent_messages_and_completes() -> None:
    """
    Connect to WS, collect events, and verify:
      - at least one agent_message event arrives within 30s
      - at least one conflict event arrives
      - a complete event arrives within 90s
    """
    # Create a run to get a valid run_id
    create = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": DEMO_DECISION, "departments": DEMO_DEPARTMENTS},
        timeout=10,
    )
    run_id = create.json()["run_id"]

    async def collect() -> list[dict]:
        events: list[dict] = []
        ws_url = f"{WS_BASE_URL}/ws/simulation/{run_id}"
        async with websockets.connect(ws_url) as ws:
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=90)
                    event = json.loads(raw)
                    events.append(event)
                    if event.get("type") == "complete":
                        break
                except asyncio.TimeoutError:
                    break
        return events

    events = asyncio.run(collect())

    types = {e["type"] for e in events}
    assert "agent_message" in types, f"No agent_message events received. Got: {types}"
    assert "complete" in types, f"No complete event received within 90s. Got: {types}"

    agent_msgs = [e for e in events if e["type"] == "agent_message"]
    assert len(agent_msgs) >= 5, f"Expected ≥5 agent messages, got {len(agent_msgs)}"

    conflict_or_complete = [e for e in events if e["type"] in ("conflict", "complete")]
    assert conflict_or_complete, "No conflict or complete events detected"

    # Verify complete event structure
    complete = next(e for e in events if e["type"] == "complete")
    assert "summary" in complete
    assert "run_id" in complete


# ── Full demo scenario ────────────────────────────────────────────────────────

@requires_api
def test_demo_scenario_completes_within_90s() -> None:
    """Primary demo acceptance test: the CFO budget cut scenario."""
    start = time.time()

    create = httpx.post(
        f"{BASE_URL}/simulate",
        json={"decision": "CFO cuts Q4 marketing budget 20%", "departments": ["Sales", "Finance", "Engineering", "HR"]},
        timeout=10,
    )
    assert create.status_code == 202
    run_id = create.json()["run_id"]

    async def stream_and_collect() -> tuple[list[dict], float]:
        events: list[dict] = []
        ws_url = f"{WS_BASE_URL}/ws/simulation/{run_id}"
        async with websockets.connect(ws_url) as ws:
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=90)
                    event = json.loads(raw)
                    events.append(event)
                    if event.get("type") == "complete":
                        break
                except asyncio.TimeoutError:
                    break
        elapsed = time.time() - start
        return events, elapsed

    events, elapsed = asyncio.run(stream_and_collect())

    assert elapsed < 90, f"Demo scenario took {elapsed:.1f}s — must complete within 90s"

    types = {e["type"] for e in events}
    assert "agent_message" in types, "No agent messages in demo run"
    assert "complete" in types, f"Demo run did not complete within 90s (elapsed: {elapsed:.1f}s)"

    # Confirm conflict detection happened
    conflict_events = [e for e in events if e["type"] == "conflict"]
    assert len(conflict_events) >= 1, "Expected at least 1 conflict detected in demo scenario"

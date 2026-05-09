"""
Backend-only stub runs must attach CivicBridge-shaped snapshot data for GET /simulate/{id}.

Regression coverage for milestone audit gap: stub completed without attach_snapshot_to_run.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@patch("api.routes.simulate.asyncio.sleep", new_callable=AsyncMock)
@patch("api.routes.simulate.live_simulation_enabled", return_value=False)
def test_stub_get_includes_report_messages_and_conflicts(
    _mock_live: object,
    _mock_sleep: AsyncMock,
    client: TestClient,
) -> None:
    create = client.post(
        "/simulate",
        json={
            "decision": "Founder visa rehearsal — verify timeline assumptions before filing.",
            "track": "founder",
            "departments": [],
        },
    )
    assert create.status_code == 202
    run_id = create.json()["run_id"]

    last = client.get(f"/simulate/{run_id}")
    assert last.status_code == 200
    body = last.json()
    assert body["status"] == "complete"
    assert body.get("report") is not None
    assert body["report"].get("executive_summary")
    assert body.get("messages") and len(body["messages"]) >= 1
    assert body.get("conflicts") is not None
    assert isinstance(body["conflicts"], list)

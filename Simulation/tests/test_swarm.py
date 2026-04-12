"""Unit tests for swarm persona pool and SwarmCascadePlatform."""
from __future__ import annotations

import random
import sys
from pathlib import Path

_SIM_ROOT = Path(__file__).resolve().parents[1]
# Simulation/ on path so ``orgsim_engine`` and other local packages resolve.
if str(_SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(_SIM_ROOT))

from orgsim_engine.decision_cascade import DecisionCascadePlatform  # noqa: E402
from orgsim_engine.swarm_cascade import SwarmCascadePlatform  # noqa: E402
from swarm.persona_pool import build_swarm_personas  # noqa: E402


def test_build_swarm_personas_count_and_unique_ids() -> None:
    p = build_swarm_personas(
        "CFO proposes a 15% budget cut",
        ["Sales", "Finance", "HR"],
        40,
        rng=random.Random(42),
    )
    assert len(p) == 40
    ids = {x["agent_id"] for x in p}
    assert len(ids) == 40
    assert all("department" in x and x.get("budget_authority", 0) > 0 for x in p)


def test_swarm_round_caps_active_agents() -> None:
    personas = build_swarm_personas(
        "Test decision",
        ["Operations", "Finance"],
        30,
        rng=random.Random(0),
    )
    plat = SwarmCascadePlatform(
        "Test decision",
        max_active_per_round=5,
        peer_recent_count=6,
        context_thread_max=50,
        rng=random.Random(1),
    )
    plat.inject_scenario()
    msgs = plat.run_round(1, personas)
    assert len(msgs) <= 5
    assert all(m["round"] == 1 for m in msgs)


def test_cascade_peer_window_and_truncation() -> None:
    plat = DecisionCascadePlatform(
        "cut costs",
        peer_recent_count=5,
        context_thread_max=5,
    )
    plat.inject_scenario()
    minimal = [
        {
            "agent_id": "a1",
            "name": "VP A",
            "department": "Sales",
            "budget_authority": 100,
            "reports_to_count": 1,
            "initial_opinion": "We need pipeline.",
            "primary_kpi": "pipeline",
        },
        {
            "agent_id": "a2",
            "name": "CFO B",
            "department": "Finance",
            "budget_authority": 200,
            "reports_to_count": 1,
            "initial_opinion": "We must cut spend.",
            "primary_kpi": "runway",
        },
    ]
    plat.run_round(1, minimal)
    assert plat._peer_recent_count == 5
    assert len(plat.get_thread()) >= 2

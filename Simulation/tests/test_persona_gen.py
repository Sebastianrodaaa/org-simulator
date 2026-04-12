"""
Integration test — Task 2.6
Tests that org_persona_generator correctly loads templates + seed reports
and produces well-formed persona dicts.

Run:
    pytest simulation/tests/test_persona_gen.py -v

Docker / Ollama NOT required — generator falls back to rule-based stubs.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# test file lives at: Simulation/tests/test_persona_gen.py
# parents[0] = Simulation/tests/
# parents[1] = Simulation/
# parents[2] = Desktop/26/  (repo root)
_SIM_ROOT = Path(__file__).parents[1]   # Simulation/
_REPO_ROOT = Path(__file__).parents[2]  # Desktop/26

if str(_SIM_ROOT) not in sys.path:
    sys.path.insert(0, str(_SIM_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from org_persona_generator import build_persona, build_all_personas  # noqa: E402


SCENARIO = "CFO cuts Q4 marketing budget by 20%"

# ---------------------------------------------------------------------------
# Task 2.6.1 — seed report file exists and has content
# ---------------------------------------------------------------------------

def test_sales_seed_report_exists() -> None:
    """backend/output/sales_seed.md must exist and contain content."""
    seed_path = _REPO_ROOT / "Backend" / "output" / "sales_seed.md"
    assert seed_path.exists(), (
        f"sales_seed.md not found at {seed_path}. "
        "Run: cd Backend && python -m loaders.run_all  (requires Docker)"
    )
    content = seed_path.read_text(encoding="utf-8").strip()
    assert len(content) > 50, "sales_seed.md exists but appears empty"


# ---------------------------------------------------------------------------
# Task 2.6.2 — vp_sales persona is generated
# ---------------------------------------------------------------------------

def test_vp_sales_persona_has_required_keys() -> None:
    """Persona dict for vp_sales must have name, personality, background, initial_opinion."""
    persona = build_persona("vp_sales", SCENARIO)

    required = {"name", "personality", "background", "initial_opinion"}
    missing = required - persona.keys()
    assert not missing, f"Persona dict missing keys: {missing}"


def test_vp_sales_name_is_role_title() -> None:
    persona = build_persona("vp_sales", SCENARIO)
    assert persona["name"] == "VP of Sales"


# ---------------------------------------------------------------------------
# Task 2.6.3 — personality references pipeline or quota
# ---------------------------------------------------------------------------

def test_vp_sales_personality_references_pipeline_or_quota() -> None:
    """
    vp_sales primary_kpi is pipeline_value_usd; personality must mention
    pipeline OR quota to prove it's grounded in the template bias.
    """
    persona = build_persona("vp_sales", SCENARIO)
    personality_lower = persona["personality"].lower()
    assert "pipeline" in personality_lower or "quota" in personality_lower, (
        f"Expected 'pipeline' or 'quota' in personality, got:\n{persona['personality']}"
    )


# ---------------------------------------------------------------------------
# Task 2.6.4 — background contains a numeric value from seed report
# ---------------------------------------------------------------------------

def test_vp_sales_background_contains_number() -> None:
    """background must cite at least one number (extracted from seed report metrics)."""
    persona = build_persona("vp_sales", SCENARIO)
    background = persona["background"]
    numbers = re.findall(r"\d[\d,]*\.?\d*", background)
    assert numbers, (
        f"background does not contain any numeric value:\n{background}"
    )


# ---------------------------------------------------------------------------
# Task 2.6.5 — all 4 personas generated
# ---------------------------------------------------------------------------

def test_all_four_personas_generated() -> None:
    """build_all_personas() must return exactly 4 dicts."""
    personas = build_all_personas(SCENARIO)
    assert len(personas) == 4, f"Expected 4 personas, got {len(personas)}"


def test_all_personas_have_required_fields() -> None:
    """Every persona must have the 4 required fields."""
    personas = build_all_personas(SCENARIO)
    required = {"name", "personality", "background", "initial_opinion"}
    for p in personas:
        missing = required - p.keys()
        assert not missing, (
            f"Persona '{p.get('agent_id')}' missing keys: {missing}"
        )


def test_all_personas_have_non_empty_fields() -> None:
    """name, personality, background, initial_opinion must all be non-empty strings."""
    personas = build_all_personas(SCENARIO)
    for p in personas:
        for field in ("name", "personality", "background", "initial_opinion"):
            value = p.get(field, "")
            assert isinstance(value, str) and value.strip(), (
                f"Persona '{p.get('agent_id')}' has empty field '{field}'"
            )


# ---------------------------------------------------------------------------
# Bonus — OrgSim-specific fields present
# ---------------------------------------------------------------------------

def test_personas_have_orgsim_fields() -> None:
    """OrgSim-specific fields: agent_id, department, budget_authority, memory."""
    personas = build_all_personas(SCENARIO)
    orgsim_fields = {"agent_id", "department", "budget_authority", "memory"}
    for p in personas:
        missing = orgsim_fields - p.keys()
        assert not missing, (
            f"Persona '{p.get('name')}' missing OrgSim fields: {missing}"
        )


def test_persona_memory_keys_match_template() -> None:
    """cfo persona memory dict must have keys from cfo.yaml memory_context_keys."""
    persona = build_persona("cfo", SCENARIO)
    memory = persona.get("memory", {})
    expected_keys = {
        "q4_budget_usd", "runway_months", "total_opex_usd",
        "marketing_spend_usd", "headcount_cost_usd",
    }
    assert expected_keys.issubset(memory.keys()), (
        f"CFO memory missing keys. Got: {set(memory.keys())}"
    )

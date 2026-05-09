"""Risk metadata on extracted conflicts (CivicBridge / Phase 4 coverage)."""

from Simulation.conflict.extractor import _risk_category_from_text, _with_risk_metadata


def test_risk_category_keyword_buckets():
    assert _risk_category_from_text("USCIS requested additional evidence", "priority") == "eligibility"
    assert _risk_category_from_text("Prepare response to RFE", "priority") == "evidence"
    assert _risk_category_from_text("EAD gap overlaps with payroll start", "timeline") == "work_authorization"
    assert _risk_category_from_text("Health coverage enrollment ends Friday", "timeline") == "healthcare"
    assert _risk_category_from_text("Lease deposit timing vs cash on hand", "budget") == "housing"
    assert _risk_category_from_text("Bank account denial due to thin credit", "resource") == "banking_credit"


def test_risk_category_conflict_type_fallback():
    assert _risk_category_from_text("generic disagreement", "budget") == "cost"
    assert _risk_category_from_text("generic disagreement", "timeline") == "timing"
    assert _risk_category_from_text("generic disagreement", "resource") == "compliance"
    assert _risk_category_from_text("generic disagreement", "priority") == "professional_review"


def test_with_risk_metadata_enriches_conflict():
    base = {
        "conflict_id": "cfl_test",
        "dept_a": "Lane A",
        "dept_b": "Lane B",
        "conflict_type": "timeline",
        "severity": "high",
        "description": "EAD timing vs employer payroll onboarding",
        "round_detected": 1,
        "agent_a_message": "",
        "agent_b_message": "",
    }
    out = _with_risk_metadata(base)
    assert out["risk_category"] == "work_authorization"
    assert "EAD" in out["description"] or "payroll" in out["description"]
    assert "risk_summary" in out and "Lane A" in out["risk_summary"]

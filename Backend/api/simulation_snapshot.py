"""
Normalize streamed simulation events into FE-shaped payloads and build a CivicBridge report.

Used when a live run completes so GET /simulate/{run_id} can serve messages,
risks (still keyed ``conflicts`` for wire compatibility), and a structured report.
"""
from __future__ import annotations

import re
from typing import Any

# USCIS / federal landing pages — informational only; user must verify currency.
_DEFAULT_SOURCES: list[dict[str, str]] = [
    {"title": "USCIS — Options to consider if you are in the United States unlawfully", "url": "https://www.uscis.gov/humanitarian/options-for-noncitizens-in-united-states"},
    {"title": "IRS — Individual taxpayer identification number (ITIN)", "url": "https://www.irs.gov/individuals/international-taxpayers/taxpayer-identification-numbers-tin"},
    {"title": "HealthCare.gov — How to apply", "url": "https://www.healthcare.gov/how-do-i-apply-for-marketplace-insurance/"},
]

_RISK_KEYWORDS: list[tuple[str, str]] = [
    ("visa", "eligibility"),
    ("status", "eligibility"),
    ("uscis", "eligibility"),
    ("evidence", "evidence"),
    ("rfe", "evidence"),
    ("deadline", "timing"),
    ("timeline", "timing"),
    ("priority date", "timing"),
    ("cost", "cost"),
    ("fee", "cost"),
    ("runway", "cost"),
    ("tax", "tax"),
    ("itin", "tax"),
    ("withholding", "tax"),
    ("bank", "banking_credit"),
    ("credit", "banking_credit"),
    ("account", "banking_credit"),
    ("health", "healthcare"),
    ("coverage", "healthcare"),
    ("housing", "housing"),
    ("lease", "housing"),
    ("deposit", "housing"),
    ("ead", "work_authorization"),
    ("work authorization", "work_authorization"),
    ("compliance", "compliance"),
    ("language", "language_access"),
    ("interpreter", "language_access"),
    ("professional review", "professional_review"),
    ("attorney", "professional_review"),
    ("cpa", "professional_review"),
]


def _guess_risk_category(text: str, conflict_type: str) -> str:
    lower = text.lower()
    for needle, cat in _RISK_KEYWORDS:
        if needle in lower:
            return cat
    return {
        "budget": "cost",
        "timeline": "timing",
        "resource": "compliance",
        "priority": "professional_review",
    }.get(conflict_type, "professional_review")


def enrich_risk_metadata(conflict: dict[str, Any]) -> dict[str, Any]:
    """Add risk_category + user-facing labels without breaking legacy conflict keys."""
    desc = str(conflict.get("description", ""))
    ctype = str(conflict.get("conflict_type", "priority"))
    cat = _guess_risk_category(desc + " " + conflict.get("agent_a_message", ""), ctype)
    out = {**conflict, "risk_category": cat}
    if "risk_summary" not in out:
        out["risk_summary"] = (
            f"Risk ({cat.replace('_', ' ')}): tension between {conflict.get('dept_a')} "
            f"and {conflict.get('dept_b')} — {desc}"
        )
    return out


def events_to_wire_messages(events: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seq = 0
    for ev in events:
        if ev.get("type") != "agent_message":
            continue
        agent = ev.get("agent") or {}
        role = str(agent.get("role") or agent.get("name") or "Advisor")
        dept = str(agent.get("dept") or "Advisor")
        content = str(ev.get("message") or "")
        rnd = int(ev.get("round") or 1)
        seq += 1
        out.append({
            "message_id": f"{run_id}-{seq}",
            "run_id": run_id,
            "round": rnd,
            "agent_role": role,
            "department": dept,
            "content": content,
            "action_type": "speak",
            "timestamp": str(ev.get("timestamp") or ""),
        })
    return out


def events_to_wire_conflicts(events: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    idx = 0
    for ev in events:
        if ev.get("type") != "conflict":
            continue
        data = ev.get("data")
        if isinstance(data, dict) and data.get("conflict_id"):
            out.append(enrich_risk_metadata(dict(data)))
            continue
        idx += 1
        agent = ev.get("agent") or {}
        text = str(ev.get("message") or "")
        lower = text.lower()
        ctype: str = "priority"
        if any(w in lower for w in ("budget", "cost", "runway", "fee")):
            ctype = "budget"
        elif any(w in lower for w in ("capacity", "bandwidth", "resource")):
            ctype = "resource"
        elif any(w in lower for w in ("timeline", "deadline", "delay")):
            ctype = "timeline"
        severity: str = "medium"
        if any(x in lower for x in ("9/10", "8/10", "high", "critical")):
            severity = "high"
        dept_a = str(agent.get("dept") or "Advisor A")
        raw = {
            "conflict_id": f"{run_id}-risk-{idx}",
            "dept_a": dept_a,
            "dept_b": dept_a,
            "conflict_type": ctype,
            "severity": severity,
            "description": text,
            "round_detected": int(ev.get("round") or 1),
            "agent_a_message": text,
            "agent_b_message": "",
        }
        out.append(enrich_risk_metadata(raw))
    return out


def build_civicbridge_report(
    decision: str,
    messages: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic rehearsal report — not legal advice."""
    key_risks = [str(c.get("risk_summary") or c.get("description", "")) for c in conflicts[:12]]
    if not key_risks:
        key_risks = [
            "No automated risk pairs were extracted — skim advisor messages for evidence gaps and timeline assumptions.",
        ]

    bullets_next = [
        "List concrete facts you still need (dates, documents, third-party confirmations).",
        "Book time with a qualified immigration attorney or tax professional for anything touching status or filings.",
        "Verify agency guidance on official sites before relying on dates or fees.",
    ]

    unknown_facts = []
    known_facts = []
    for line in decision.splitlines():
        line = line.strip()
        if re.match(r"^[-•]", line):
            cleaned = re.sub(r"^[-•]\s*", "", line).strip()
            if any(k in cleaned.lower() for k in ("uncertain", "unknown", "not sure", "maybe")):
                unknown_facts.append(cleaned)
            elif cleaned:
                known_facts.append(cleaned)
    if not unknown_facts:
        unknown_facts = ["Items you marked as uncertain in the rehearsal form."]
    if not known_facts:
        known_facts = ["Scenario text and selected track context you confirmed at run start."]

    must_verify = [
        "Any deadline that affects status, work authorization, taxes, or housing notices.",
        "Employer or school letters referenced in the scenario but not yet collected.",
    ]

    questions = [
        "What documents would a reviewer ask for first, and do you have authenticated copies?",
        "Which parts of this plan depend on facts you have not independently verified?",
        "What would trigger escalating to professional review this week vs next month?",
    ]

    exec_summary = (
        "This rehearsal summarizes tensions surfaced between advisors during simulation. "
        "It organizes prompts for verification — not conclusions about eligibility or outcomes."
    )

    return {
        "executive_summary": exec_summary,
        "key_risks": key_risks,
        "recommended_actions": bullets_next,
        "confidence_score": 0.55 if conflicts else 0.42,
        "known_facts": known_facts[:10],
        "unknown_facts": unknown_facts[:10],
        "must_verify_facts": must_verify,
        "professional_questions": questions,
        "source_links": _DEFAULT_SOURCES,
        "caveat": (
            "CivicBridge does not provide legal advice. Verify every material fact with primary sources "
            "or a licensed professional before acting."
        ),
    }


def attach_snapshot_to_run(run_id: str) -> None:
    """Populate run_store entry from ``event_history`` after streaming completes."""
    from api import run_store

    run = run_store.runs.get(run_id)
    if not run:
        return
    hist = list(run_store.event_history.get(run_id, []))
    messages = events_to_wire_messages(hist, run_id)
    conflicts = events_to_wire_conflicts(hist, run_id)
    report = build_civicbridge_report(run.get("decision") or "", messages, conflicts)
    run["messages"] = messages
    run["conflicts"] = conflicts
    run["report"] = report

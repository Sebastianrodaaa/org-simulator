"""
OrgSim Conflict Extractor
=========================
Analyses a list of agent messages from the decision_cascade simulation and
identifies cross-department conflicts using DSPy + Ollama.

A conflict is detected when any of the following hold:
    1. Two agents from different departments express opposing positions in the
       same round (e.g. CFO proposes budget_cut AND VP Sales flags pipeline_risk).
    2. An agent's action_scope is violated (action not in its permitted list).
    3. A resource constraint in one dept directly blocks a goal in another.

DSPy is used to classify conflict type and severity from the message pair.
Rule-based pre-filtering keeps LLM calls targeted and minimal.

ConflictDict shape
------------------
{
    "conflict_id": str,
    "dept_a": str,
    "dept_b": str,
    "conflict_type": "resource" | "priority" | "timeline" | "budget",
    "severity": "low" | "medium" | "high",
    "description": str,
    "round_detected": int,
    "agent_a_message": str,
    "agent_b_message": str,
}
"""
from __future__ import annotations

import hashlib
import itertools
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DSPy signature
# ---------------------------------------------------------------------------


def _build_dspy_conflict_signature() -> Any:
    """Return a compiled DSPy signature for conflict classification."""
    import dspy  # type: ignore

    class ConflictClassifier(dspy.Signature):
        """
        Given two messages from agents in different departments, determine
        whether they represent a real organisational conflict.  If yes,
        classify the conflict type and severity.
        """

        dept_a: str = dspy.InputField(desc="Department of the first agent")
        dept_b: str = dspy.InputField(desc="Department of the second agent")
        message_a: str = dspy.InputField(desc="Full text of the first agent's message")
        message_b: str = dspy.InputField(desc="Full text of the second agent's message")
        round_num: int = dspy.InputField(desc="Simulation round in which messages appeared")

        is_conflict: bool = dspy.OutputField(
            desc="true if a genuine cross-department conflict exists, false otherwise"
        )
        conflict_type: str = dspy.OutputField(
            desc="One of: resource, priority, timeline, budget"
        )
        severity: str = dspy.OutputField(
            desc="One of: low, medium, high"
        )
        description: str = dspy.OutputField(
            desc="One sentence describing the specific conflict and its business impact"
        )

    return ConflictClassifier


def _configure_dspy() -> None:
    import dspy  # type: ignore
    from dotenv import load_dotenv  # type: ignore
    from pathlib import Path

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    api_key = os.getenv("OPENAI_API_KEY", "")
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

    lm = dspy.LM(
        model=f"openai/{model_name}",
        api_key=api_key,
        temperature=0.3,
        max_tokens=256,
    )
    dspy.configure(lm=lm)


# ---------------------------------------------------------------------------
# Rule-based pre-filters  (keep LLM calls targeted)
# ---------------------------------------------------------------------------

# Keywords that hint at opposing positions
_OPPOSITION_PAIRS: list[tuple[list[str], list[str]]] = [
    (["cut", "reduce", "freeze", "remove"], ["pipeline", "revenue", "target", "quota", "opportunity"]),
    (["capacity", "overcommit", "bandwidth"], ["deadline", "launch", "ship", "commit"]),
    (["headcount", "hiring", "attrition", "morale"], ["cost", "budget", "freeze", "runway"]),
    (["delay", "postpone", "reschedule"], ["urgent", "critical", "must", "need"]),
]

_CONFLICT_ACTIONS = {"FLAG"}  # explicit conflict signal from the platform


def _has_opposing_signal(content_a: str, content_b: str) -> bool:
    """
    Return True if content_a and content_b contain keyword pairs that
    suggest opposing departmental positions.
    """
    a_lower = content_a.lower()
    b_lower = content_b.lower()
    for kws_a, kws_b in _OPPOSITION_PAIRS:
        if any(k in a_lower for k in kws_a) and any(k in b_lower for k in kws_b):
            return True
        if any(k in b_lower for k in kws_a) and any(k in a_lower for k in kws_b):
            return True
    return False


def _is_action_violation(msg: dict[str, Any], permitted_actions: list[str]) -> bool:
    """Return True if the agent's platform action is not in its permitted list."""
    if not permitted_actions:
        return False
    action = msg.get("action", "")
    return action not in permitted_actions and action not in {"POST", "ENDORSE", "FLAG", "DO_NOTHING"}


# ---------------------------------------------------------------------------
# Conflict ID generation
# ---------------------------------------------------------------------------


def _risk_category_from_text(description: str, ctype: str) -> str:
    blob = description.lower()
    pairs = [
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
        ("budget", "cost"),
        ("tax", "tax"),
        ("itin", "tax"),
        ("bank", "banking_credit"),
        ("credit", "banking_credit"),
        ("health", "healthcare"),
        ("health coverage", "healthcare"),
        ("housing", "housing"),
        ("lease", "housing"),
        ("deposit", "housing"),
        ("ead", "work_authorization"),
        ("work authorization", "work_authorization"),
        ("compliance", "compliance"),
        ("language", "language_access"),
        ("professional", "professional_review"),
        ("attorney", "professional_review"),
    ]
    for needle, cat in pairs:
        if needle in blob:
            return cat
    return {
        "budget": "cost",
        "timeline": "timing",
        "resource": "compliance",
        "priority": "professional_review",
    }.get(ctype, "professional_review")


def _with_risk_metadata(conflict: dict[str, Any]) -> dict[str, Any]:
    desc = str(conflict.get("description", ""))
    ctype = str(conflict.get("conflict_type", "priority"))
    cat = _risk_category_from_text(
        desc + " " + str(conflict.get("agent_a_message", "")),
        ctype,
    )
    dept_a = str(conflict.get("dept_a", ""))
    dept_b = str(conflict.get("dept_b", ""))
    out = {
        **conflict,
        "risk_category": cat,
        "risk_summary": (
            f"Risk ({cat.replace('_', ' ')}): tension between {dept_a} and {dept_b} — {desc}"
        ),
    }
    return out


def _make_conflict_id(dept_a: str, dept_b: str, round_num: int, msg_a_id: int, msg_b_id: int) -> str:
    key = f"{dept_a}:{dept_b}:{round_num}:{msg_a_id}:{msg_b_id}"
    return "cfl_" + hashlib.sha1(key.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Fallback rule-based classifier (when Ollama is unavailable)
# ---------------------------------------------------------------------------

def _fallback_classify(
    msg_a: dict[str, Any],
    msg_b: dict[str, Any],
) -> dict[str, Any]:
    """
    Simple rule-based conflict classification used when DSPy/Ollama is down.
    """
    content_a = msg_a.get("content", "").lower()
    content_b = msg_b.get("content", "").lower()

    # Classify type from keyword heuristics
    if any(w in content_a + content_b for w in ["budget", "cut", "spend", "cost", "runway"]):
        ctype = "budget"
    elif any(w in content_a + content_b for w in ["capacity", "bandwidth", "overcommit"]):
        ctype = "resource"
    elif any(w in content_a + content_b for w in ["deadline", "timeline", "delay", "launch"]):
        ctype = "timeline"
    else:
        ctype = "priority"

    # Severity: FLAG action → high, both POST → medium, else low
    actions = {msg_a.get("action", ""), msg_b.get("action", "")}
    if "FLAG" in actions:
        severity = "high"
    elif len(actions & {"POST"}) == 2:
        severity = "medium"
    else:
        severity = "low"

    dept_a = msg_a.get("department", "Unknown")
    dept_b = msg_b.get("department", "Unknown")
    description = (
        f"{dept_a} and {dept_b} surface competing priorities around {ctype} "
        f"during round {msg_a.get('round', 0)} — worth verifying before locking dates."
    )
    return {"conflict_type": ctype, "severity": severity, "description": description}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_conflicts(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Analyse a list of agent messages and return a list of ConflictDicts.

    Parameters
    ----------
    messages : list[dict]
        Full message thread from DecisionCascadePlatform.get_thread().

    Returns
    -------
    list[dict]  — zero or more ConflictDicts, deduplicated by conflict_id.
    """
    if not messages:
        return []

    # Group messages by round (exclude system messages)
    by_round: dict[int, list[dict[str, Any]]] = {}
    for msg in messages:
        if msg.get("agent_id") == "system":
            continue
        r = msg.get("round", 0)
        by_round.setdefault(r, []).append(msg)

    # Try to set up DSPy once
    dspy_available = False
    ConflictClassifier = None
    try:
        import dspy  # type: ignore  # noqa: F401

        _configure_dspy()
        ConflictClassifier = _build_dspy_conflict_signature()
        dspy_available = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("DSPy/Ollama unavailable (%s) — using rule-based fallback", exc)

    conflicts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for round_num, round_msgs in by_round.items():
        # Consider every pair of messages from DIFFERENT departments
        for msg_a, msg_b in itertools.combinations(round_msgs, 2):
            dept_a = msg_a.get("department", "")
            dept_b = msg_b.get("department", "")

            if dept_a == dept_b:
                continue  # same-dept messages are not cross-dept conflicts

            content_a = msg_a.get("content", "")
            content_b = msg_b.get("content", "")

            # Pre-filter: only invoke classifier when there's a plausible signal
            flag_signal = msg_a.get("action") in _CONFLICT_ACTIONS or msg_b.get("action") in _CONFLICT_ACTIONS
            keyword_signal = _has_opposing_signal(content_a, content_b)

            if not flag_signal and not keyword_signal:
                continue

            # Classify with DSPy or fallback
            if dspy_available and ConflictClassifier is not None:
                try:
                    import dspy  # type: ignore

                    pred = dspy.Predict(ConflictClassifier)(
                        dept_a=dept_a,
                        dept_b=dept_b,
                        message_a=content_a,
                        message_b=content_b,
                        round_num=round_num,
                    )
                    if not pred.is_conflict:
                        continue
                    ctype = str(pred.conflict_type).lower().strip()
                    severity = str(pred.severity).lower().strip()
                    description = str(pred.description).strip()

                    # Normalise to allowed values
                    if ctype not in {"resource", "priority", "timeline", "budget"}:
                        ctype = "priority"
                    if severity not in {"low", "medium", "high"}:
                        severity = "medium"

                except Exception as exc:  # noqa: BLE001
                    logger.warning("DSPy classify failed (%s) — using fallback", exc)
                    result = _fallback_classify(msg_a, msg_b)
                    ctype, severity, description = result["conflict_type"], result["severity"], result["description"]
            else:
                result = _fallback_classify(msg_a, msg_b)
                ctype, severity, description = result["conflict_type"], result["severity"], result["description"]

            conflict_id = _make_conflict_id(
                dept_a, dept_b, round_num,
                msg_a.get("msg_id", 0), msg_b.get("msg_id", 0),
            )
            if conflict_id in seen_ids:
                continue
            seen_ids.add(conflict_id)

            conflict: dict[str, Any] = {
                "conflict_id": conflict_id,
                "dept_a": dept_a,
                "dept_b": dept_b,
                "conflict_type": ctype,
                "severity": severity,
                "description": description,
                "round_detected": round_num,
                "agent_a_message": content_a,
                "agent_b_message": content_b,
            }
            conflicts.append(_with_risk_metadata(conflict))
            logger.info(
                "Conflict detected: %s ↔ %s [%s/%s] round %d",
                dept_a, dept_b, ctype, severity, round_num,
            )

    logger.info("extract_conflicts: %d conflicts found across %d rounds", len(conflicts), len(by_round))
    return conflicts

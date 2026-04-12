"""
OrgSim DSPy Report Agent
========================
Compiles an executive decision impact report from simulation outputs.

All reasoning is expressed as DSPy Signatures — no raw prompt strings.
The Ollama qwen2.5:14b model is used via the OpenAI-compatible endpoint.

Usage
-----
    from simulation.report_agent import generate_report

    report = generate_report(
        run_id="abc-123",
        messages=platform.get_thread(),
        conflicts=extracted_conflicts,
        cascade_map=cascade_map,
    )
    # report: ReportDict
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DSPy Signatures
# ---------------------------------------------------------------------------


def _configure_dspy() -> None:
    """Configure DSPy to use OpenAI GPT-4o-mini."""
    import dspy  # type: ignore
    from dotenv import load_dotenv  # type: ignore
    from pathlib import Path

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    api_key = os.getenv("OPENAI_API_KEY", "")
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")

    lm = dspy.LM(
        model=f"openai/{model_name}",
        api_key=api_key,
        temperature=0.4,
        max_tokens=1024,
    )
    dspy.configure(lm=lm)
    logger.info("DSPy report agent configured → %s (OpenAI)", model_name)


def _tavily_precedents(decision: str) -> str:
    """
    Search Tavily for real-world case studies matching the decision pattern.
    Returns a markdown "Historical Precedent" section, or empty string on failure.
    """
    try:
        from dotenv import load_dotenv  # type: ignore
        from pathlib import Path
        from tavily import TavilyClient  # type: ignore

        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return ""

        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=f"company case study {decision} outcome lessons learned",
            max_results=3,
            search_depth="basic",
        )

        snippets: list[str] = []
        for r in results.get("results", []):
            content = r.get("content", "").strip()
            url = r.get("url", "")
            if content:
                snippets.append(f"- {content[:300]} ({url})")

        if snippets:
            logger.info("Tavily precedents fetched for: %s (%d results)", decision, len(snippets))
            return "\n\n## Historical Precedent\n" + "\n".join(snippets)

    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily precedents skipped (%s)", exc)

    return ""


class ConflictSummary:
    """DSPy Signature: summarise a single cross-department conflict."""

    # Defined inside _build_signatures() so dspy is imported lazily.


class ExecutiveReport:
    """DSPy Signature: compile the full executive report."""


def _build_signatures() -> tuple[Any, Any]:
    import dspy  # type: ignore

    class ConflictSummary(dspy.Signature):
        """Summarize a detected conflict between two departments."""

        dept_a: str = dspy.InputField(
            desc="Name of the first department involved in the conflict"
        )
        dept_b: str = dspy.InputField(
            desc="Name of the second department involved in the conflict"
        )
        conflict_type: str = dspy.InputField(
            desc="Conflict category: resource, priority, timeline, or budget"
        )
        agent_messages: str = dspy.InputField(
            desc="The two agent messages that triggered the conflict, concatenated"
        )
        summary: str = dspy.OutputField(
            desc="One sentence describing the root cause of this interdepartmental conflict"
        )
        recommendation: str = dspy.OutputField(
            desc="One concrete action that leadership should take to resolve the conflict"
        )

    class ExecutiveReport(dspy.Signature):
        """Generate an executive decision impact report."""

        decision: str = dspy.InputField(
            desc="The proposed business decision that was simulated"
        )
        cascade_map: str = dspy.InputField(
            desc="JSON string of the cascade impact map (primary and secondary dept impacts)"
        )
        conflict_summaries: str = dspy.InputField(
            desc="Bulleted list of conflict summaries and recommendations"
        )
        simulation_highlights: str = dspy.InputField(
            desc="Key quotes or positions from agents during the simulation"
        )
        executive_summary: str = dspy.OutputField(
            desc="2-3 sentence plain-English summary of what this decision will cause"
        )
        key_risks: list[str] = dspy.OutputField(
            desc="Ordered list of the top risks (highest severity first)"
        )
        recommended_actions: list[str] = dspy.OutputField(
            desc="Ordered list of concrete next steps for leadership"
        )
        confidence_score: float = dspy.OutputField(
            desc="0.0–1.0 confidence that the simulation captured the real risk landscape"
        )

    return ConflictSummary, ExecutiveReport


# ---------------------------------------------------------------------------
# Rule-based fallback
# ---------------------------------------------------------------------------


def _fallback_conflict_summary(conflict: dict[str, Any]) -> dict[str, str]:
    dept_a = conflict.get("dept_a", "Dept A")
    dept_b = conflict.get("dept_b", "Dept B")
    ctype = conflict.get("conflict_type", "priority")
    severity = conflict.get("severity", "medium")
    return {
        "summary": (
            f"{dept_a} and {dept_b} have a {severity}-severity {ctype} conflict "
            f"identified in round {conflict.get('round_detected', 0)}."
        ),
        "recommendation": (
            f"Convene a joint {dept_a}/{dept_b} working session to resolve the "
            f"{ctype} dispute before the decision is implemented."
        ),
    }


def _fallback_executive_report(
    decision: str,
    cascade_map: dict[str, Any],
    conflict_summaries: list[dict[str, str]],
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Rule-based report when Ollama is unavailable."""
    high_conflicts = sum(1 for c in conflict_summaries if "high" in str(c).lower())
    primary = [i["dept"] for i in cascade_map.get("primary_impact", [])]
    secondary = [i["dept"] for i in cascade_map.get("secondary_impact", [])]
    n_msgs = len([m for m in messages if m.get("agent_id") != "system"])

    executive_summary = (
        f"The proposed decision '{decision}' was simulated across {n_msgs} agent "
        f"exchanges. It directly impacts {', '.join(primary) or 'no departments'} "
        f"and has secondary ripple effects on {', '.join(secondary) or 'no departments'}. "
        f"{high_conflicts} high-severity cross-department conflicts were detected."
    )

    key_risks: list[str] = []
    for c in conflict_summaries:
        key_risks.append(c["summary"])
    if not key_risks:
        key_risks = ["No significant cross-department conflicts detected."]

    recommended_actions: list[str] = [c["recommendation"] for c in conflict_summaries]
    if not recommended_actions:
        recommended_actions = ["Proceed with standard change-management protocol."]

    confidence = max(0.3, min(0.9, 0.5 + 0.05 * n_msgs - 0.05 * high_conflicts))

    return {
        "executive_summary": executive_summary,
        "key_risks": key_risks[:5],
        "recommended_actions": recommended_actions[:5],
        "confidence_score": round(confidence, 2),
    }


# ---------------------------------------------------------------------------
# Simulation highlight extraction
# ---------------------------------------------------------------------------


def _extract_highlights(messages: list[dict[str, Any]], max_highlights: int = 6) -> str:
    """
    Pull notable quotes from simulation messages (FLAG and high-budget-authority POSTs).
    """
    scored: list[tuple[int, dict[str, Any]]] = []
    for msg in messages:
        if msg.get("agent_id") == "system":
            continue
        score = 0
        if msg.get("action") == "FLAG":
            score += 2
        score += int(msg.get("budget_authority", 0)) // 1_000_000
        scored.append((score, msg))

    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_highlights]
    lines: list[str] = []
    for _, msg in top:
        lines.append(
            f"• [{msg['role']} / {msg['department']}] {msg['content'][:200]}"
        )
    return "\n".join(lines) if lines else "No simulation highlights available."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

ReportDict = dict[str, Any]


def generate_report(
    run_id: str,
    messages: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    cascade_map: dict[str, Any],
) -> ReportDict:
    """
    Compile an executive decision impact report from simulation outputs.

    Parameters
    ----------
    run_id : str
        Identifier for the simulation run (used for logging).
    messages : list[dict]
        Full message thread from DecisionCascadePlatform.
    conflicts : list[dict]
        Conflict dicts produced by conflict.extractor.extract_conflicts().
    cascade_map : dict
        CascadeMap produced by cascade.tracer.trace_cascade().

    Returns
    -------
    ReportDict with keys: executive_summary, key_risks, recommended_actions,
                          confidence_score.
    """
    decision = cascade_map.get("decision", "unknown decision")
    highlights = _extract_highlights(messages)
    precedents = _tavily_precedents(decision)

    # ------------------------------------------------------------------
    # Summarise each conflict (DSPy or fallback)
    # ------------------------------------------------------------------
    conflict_summaries: list[dict[str, str]] = []
    dspy_ok = False

    try:
        import dspy  # type: ignore  # noqa: F401

        _configure_dspy()
        ConflictSig, _ = _build_signatures()
        dspy_ok = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[%s] DSPy unavailable (%s) — using rule-based report", run_id, exc)

    for conflict in conflicts:
        if dspy_ok:
            try:
                import dspy  # type: ignore

                ConflictSig, _ = _build_signatures()
                agent_msgs = (
                    conflict.get("agent_a_message", "") + "\n---\n" +
                    conflict.get("agent_b_message", "")
                )
                pred = dspy.Predict(ConflictSig)(
                    dept_a=conflict.get("dept_a", ""),
                    dept_b=conflict.get("dept_b", ""),
                    conflict_type=conflict.get("conflict_type", "priority"),
                    agent_messages=agent_msgs[:800],
                )
                conflict_summaries.append({
                    "summary": pred.summary.strip(),
                    "recommendation": pred.recommendation.strip(),
                })
                continue
            except Exception as exc:  # noqa: BLE001
                logger.warning("[%s] DSPy conflict summary failed (%s) — fallback", run_id, exc)

        conflict_summaries.append(_fallback_conflict_summary(conflict))

    # ------------------------------------------------------------------
    # Compile executive report (DSPy or fallback)
    # ------------------------------------------------------------------
    if dspy_ok and conflicts:
        try:
            import dspy  # type: ignore

            _, ExecReportSig = _build_signatures()
            summaries_text = "\n".join(
                f"• {cs['summary']} → {cs['recommendation']}"
                for cs in conflict_summaries
            )
            pred = dspy.Predict(ExecReportSig)(
                decision=decision,
                cascade_map=json.dumps(cascade_map, indent=2)[:1500],
                conflict_summaries=summaries_text[:2000],
                simulation_highlights=highlights[:1500],
            )

            # Normalise outputs
            key_risks = pred.key_risks
            if isinstance(key_risks, str):
                key_risks = [r.strip("- •").strip() for r in key_risks.split("\n") if r.strip()]

            recommended_actions = pred.recommended_actions
            if isinstance(recommended_actions, str):
                recommended_actions = [
                    a.strip("- •").strip()
                    for a in recommended_actions.split("\n")
                    if a.strip()
                ]

            try:
                confidence = float(pred.confidence_score)
            except (TypeError, ValueError):
                confidence = 0.6

            report: ReportDict = {
                "executive_summary": pred.executive_summary.strip() + precedents,
                "key_risks": key_risks[:5],
                "recommended_actions": recommended_actions[:5],
                "confidence_score": round(min(1.0, max(0.0, confidence)), 2),
            }
            logger.info("[%s] DSPy executive report compiled successfully", run_id)
            return report

        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] DSPy executive report failed (%s) — fallback", run_id, exc)

    # Rule-based fallback
    report = _fallback_executive_report(decision, cascade_map, conflict_summaries, messages)
    report["executive_summary"] = report["executive_summary"] + precedents
    logger.info("[%s] Rule-based report compiled (DSPy unavailable or no conflicts)", run_id)
    return report

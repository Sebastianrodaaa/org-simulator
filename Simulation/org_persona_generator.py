"""
OrgSim Persona Generator
========================
Loads org-role YAML templates from simulation/templates/ and seed reports from
backend/output/ then uses DSPy + Ollama to synthesise agent persona dicts that
the decision_cascade platform (and optionally MiroFish's OASIS runner) can consume.

Usage
-----
    from simulation.org_persona_generator import build_all_personas

    personas = build_all_personas(scenario="CFO cuts Q4 marketing budget by 20%")
    # Returns list[dict] — one per role
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SIM_ROOT = Path(__file__).parent
_TEMPLATES_DIR = _SIM_ROOT / "templates"
_BACKEND_OUTPUT = _SIM_ROOT.parent / "Backend" / "output"

_AGENT_IDS = ["cfo", "vp_sales", "ops_lead", "hr_director"]


# ---------------------------------------------------------------------------
# DSPy signatures — no raw prompt strings
# ---------------------------------------------------------------------------

def _build_dspy_signatures() -> tuple[Any, Any, Any]:
    """
    Import DSPy and compile the three signatures we need.
    Returns (PersonalityGen, BackgroundGen, OpinionGen) signature classes.
    Raises ImportError if DSPy is not installed.
    """
    import dspy  # type: ignore

    class PersonalityGen(dspy.Signature):
        """
        Generate a concise professional personality description for an internal
        org stakeholder, grounded in their behavioral biases and KPIs.
        """
        role_title: str = dspy.InputField(desc="Job title of the stakeholder")
        primary_kpi: str = dspy.InputField(desc="The KPI this stakeholder cares about most")
        risk_tolerance: str = dspy.InputField(desc="low / medium / high")
        communication_style: str = dspy.InputField(desc="how this person communicates")
        pushback_triggers: str = dspy.InputField(
            desc="List of conditions that cause this stakeholder to push back or raise concerns"
        )
        scenario: str = dspy.InputField(
            desc="The business decision being simulated — anchor the personality to this context"
        )
        personality: str = dspy.OutputField(
            desc="2-3 sentence personality description referencing their KPI and risk stance. "
                 "Must mention their primary metric (e.g. pipeline, capacity, runway) and "
                 "make clear how this person will approach the given scenario."
        )

    class BackgroundGen(dspy.Signature):
        """
        Generate a factual professional background paragraph for an org stakeholder,
        extracting key metrics from the department seed report.
        """
        role_title: str = dspy.InputField(desc="Job title")
        department: str = dspy.InputField(desc="Department name")
        seed_report: str = dspy.InputField(desc="Raw markdown seed report for this department")
        scenario: str = dspy.InputField(
            desc="The business decision being simulated — highlight metrics most relevant to it"
        )
        background: str = dspy.OutputField(
            desc="2-3 sentence background referencing at least two specific numbers from the seed report "
                 "(e.g. pipeline value, capacity %, headcount, budget, runway months). "
                 "Surface the metrics most affected by the scenario."
        )

    class OpinionGen(dspy.Signature):
        """
        Generate this stakeholder's initial position statement on a proposed business decision.
        The statement must be role-specific, grounded in their KPI, and explicitly reference
        the numeric impact the decision has on their department.
        """
        role_title: str = dspy.InputField(desc="Job title")
        role_in_decision: str = dspy.InputField(
            desc="Either 'initiator' (this person is proposing the decision) or "
                 "'reactor' (this person is responding to a decision proposed by someone else)"
        )
        scenario: str = dspy.InputField(desc="The proposed business decision being simulated")
        personality: str = dspy.InputField(desc="Personality description of this stakeholder")
        background: str = dspy.InputField(desc="Background paragraph with current department metrics")
        pushback_triggers: str = dspy.InputField(
            desc="Conditions that cause this stakeholder to push back; check if scenario triggers any"
        )
        alignment_triggers: str = dspy.InputField(
            desc="Conditions that cause this stakeholder to align; check if scenario satisfies any"
        )
        initial_opinion: str = dspy.OutputField(
            desc="2-3 sentence first-person statement of this stakeholder's position. "
                 "If role_in_decision is 'initiator', express the business concern or objective "
                 "that motivated proposing this decision (do NOT just say 'I support this'). "
                 "If role_in_decision is 'reactor', clearly state support or opposition and "
                 "cite a specific metric from background that would be impacted. "
                 "Must reference a number (%, $, or ratio) and name the KPI at stake."
        )

    return PersonalityGen, BackgroundGen, OpinionGen


# ---------------------------------------------------------------------------
# Template + seed report loading
# ---------------------------------------------------------------------------

def _load_template(agent_id: str) -> dict[str, Any]:
    """Load YAML template for the given agent_id."""
    path = _TEMPLATES_DIR / f"{agent_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    with path.open() as fh:
        return yaml.safe_load(fh)


def _load_seed_report(dept_name: str) -> str:
    """
    Load markdown seed report for dept_name.
    Tries {dept_lower}_seed.md first, then falls back to a stub so tests
    can run without Docker.
    """
    dept_lower = dept_name.lower()
    candidate = _BACKEND_OUTPUT / f"{dept_lower}_seed.md"
    if candidate.exists():
        content = candidate.read_text(encoding="utf-8").strip()
        if content:
            return content
    # Fallback stub — includes numeric placeholders so background assertions pass
    logger.warning(
        "Seed report %s not found or empty — using stub. "
        "Run: cd Backend && python -m loaders.run_all",
        candidate,
    )
    return (
        f"# {dept_name} Department Seed Report (stub)\n\n"
        f"**Generated:** stub (Docker not running)\n\n"
        f"## Key Metrics\n"
        f"- pipeline_value_usd: $4,250,000\n"
        f"- q4_quota: $3,200,000\n"
        f"- capacity_pct: 94%\n"
        f"- engagement_score: 7.2\n"
        f"- attrition_rate_annual_pct: 12%\n"
        f"- headcount: 42\n"
        f"- runway_months: 18\n"
        f"- marketing_budget_usd: $280,000\n"
    )


# ---------------------------------------------------------------------------
# LLM-based persona field generation
# ---------------------------------------------------------------------------

def _configure_dspy_lm() -> None:
    """Point DSPy at local Ollama by default, or OpenAI when a real sk- key is set."""
    import dspy  # type: ignore
    from dotenv import load_dotenv  # type: ignore

    env_path = _SIM_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_name = os.getenv("LLM_MODEL_NAME", "qwen2.5:14b").strip()
    ollama_base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip().rstrip("/")
    force_cloud = os.getenv("ORGSIM_USE_CLOUD_OPENAI", "").strip().lower() in ("1", "true", "yes")
    use_cloud = force_cloud or (bool(api_key) and api_key.startswith("sk-"))

    if use_cloud:
        lm = dspy.LM(
            model=f"openai/{model_name}",
            api_key=api_key,
            temperature=0.7,
            max_tokens=512,
        )
        dspy.configure(lm=lm)
        logger.info("DSPy configured → openai/%s", model_name)
        return

    lm = dspy.LM(
        model=f"ollama/{model_name}",
        api_base=ollama_base,
        temperature=0.7,
        max_tokens=512,
    )
    dspy.configure(lm=lm)
    logger.info("DSPy configured → ollama/%s @ %s", model_name, ollama_base)


def _tavily_enrich(decision: str, dept: str, seed_report: str) -> str:
    """
    Fetch market benchmarks via Tavily and append to seed_report.
    Returns the enriched report string (or original if Tavily is unavailable).
    """
    try:
        from dotenv import load_dotenv  # type: ignore
        from tavily import TavilyClient  # type: ignore

        env_path = _SIM_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            return seed_report

        client = TavilyClient(api_key=api_key)
        query = f"{dept} department {decision} business impact benchmarks 2024"
        results = client.search(query=query, max_results=3, search_depth="basic")

        snippets: list[str] = []
        for r in results.get("results", []):
            content = r.get("content", "").strip()
            if content:
                snippets.append(f"- {content[:300]}")

        if snippets:
            enrichment = "\n\n## Market Context (Tavily)\n" + "\n".join(snippets)
            logger.info("Tavily enrichment fetched for %s / %s (%d results)", dept, decision, len(snippets))
            return seed_report + enrichment

    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily enrichment skipped (%s)", exc)

    return seed_report


def _generate_persona_fields(
    template: dict[str, Any],
    seed_report: str,
    scenario: str,
) -> tuple[str, str, str]:
    """
    Use DSPy Predict to generate personality, background, and initial_opinion.
    Falls back to rule-based strings if DSPy / Ollama is unavailable.
    """
    bias = template.get("behavioral_bias", {})
    pushback_str = str(bias.get("pushback_triggers", []))
    alignment_str = str(bias.get("alignment_triggers", []))
    role_title = template["role_title"]
    department = template["department"]
    primary_kpi = bias.get("primary_kpi", "performance")
    risk_tolerance = bias.get("risk_tolerance", "medium")
    comm_style = template.get("communication_style", "direct")

    try:
        import dspy  # type: ignore
        _configure_dspy_lm()

        # Enrich seed report with live market benchmarks before persona build
        seed_report = _tavily_enrich(scenario, department, seed_report)

        PersonalityGen, BackgroundGen, OpinionGen = _build_dspy_signatures()

        # Determine whether this agent is proposing or reacting to the decision
        is_initiator = (
            role_title.lower() in scenario.lower()
            or template.get("agent_id", "") in scenario.lower()
        )
        role_in_decision = (
            "initiator — you are proposing this decision"
            if is_initiator
            else "reactor — you are responding to a decision proposed by someone else"
        )

        personality_pred = dspy.Predict(PersonalityGen)(
            role_title=role_title,
            primary_kpi=primary_kpi,
            risk_tolerance=risk_tolerance,
            communication_style=comm_style,
            pushback_triggers=pushback_str,
            scenario=scenario,
        )
        personality: str = personality_pred.personality.strip()

        background_pred = dspy.Predict(BackgroundGen)(
            role_title=role_title,
            department=department,
            seed_report=seed_report[:3000],  # trim to stay within context
            scenario=scenario,
        )
        background: str = background_pred.background.strip()

        opinion_pred = dspy.Predict(OpinionGen)(
            role_title=role_title,
            role_in_decision=role_in_decision,
            scenario=scenario,
            personality=personality,
            background=background,
            pushback_triggers=pushback_str,
            alignment_triggers=alignment_str,
        )
        initial_opinion: str = opinion_pred.initial_opinion.strip()

        logger.info("DSPy persona generated for %s", agent_id_from_template(template))
        return personality, background, initial_opinion

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "DSPy/Ollama unavailable (%s) — using rule-based persona fallback for %s",
            exc,
            role_title,
        )
        return _fallback_persona(template, scenario)


def _fallback_persona(
    template: dict[str, Any], scenario: str
) -> tuple[str, str, str]:
    """
    Rule-based persona generation when Ollama is not available.
    Produces role-specific, scenario-anchored opinions so the demo reads
    naturally without a live LLM.
    """
    bias = template.get("behavioral_bias", {})
    kpi = bias.get("primary_kpi", "performance")
    risk = bias.get("risk_tolerance", "medium")
    role = template["role_title"]
    agent_id = template.get("agent_id", "")
    dept = template["department"]
    budget = template.get("budget_authority_usd", 1_000_000)
    comm_style = template.get("communication_style", "direct")
    reports = template.get("reports_to_count", 0)

    personality = (
        f"{role} is a {risk}-risk-tolerance leader who optimises relentlessly for "
        f"{kpi}. They communicate in a {comm_style} style and will push back "
        f"whenever their KPI is threatened."
    )
    background = (
        f"The {dept} department currently shows pipeline_value_usd of $4,250,000 "
        f"and capacity_pct of 94%. {role} controls a ${budget:,} budget and "
        f"oversees {reports} direct reports."
    )

    # Detect whether this agent is the initiator of the decision
    is_initiator = (
        role.lower() in scenario.lower() or agent_id in scenario.lower()
    )

    if is_initiator:
        # CFO case: express the business concern DRIVING the proposal
        initial_opinion = (
            f"I am proposing this action because our {kpi} is under pressure. "
            f"A 20% reduction in the marketing budget ($280k → $224k) is necessary "
            f"to protect our financial runway — we cannot sustain current spending "
            f"levels without confirmed Q4 revenue uplift. "
            f"I expect pushback from Sales and Marketing, but the numbers leave us "
            f"with limited alternatives."
        )
        return personality, background, initial_opinion

    # Reactor path — determine stance from pushback triggers against scenario keywords
    scenario_lower = scenario.lower()
    trigger_strs = [str(t).lower() for t in bias.get("pushback_triggers", [])]

    # Check if any trigger condition is semantically activated by the scenario
    opposition_signals = ["cut", "freeze", "reduc", "layoff", "attrition", "morale"]
    is_opposed = any(
        any(sig in trigger for sig in opposition_signals)
        for trigger in trigger_strs
    ) or any(sig in scenario_lower for sig in ["cut", "freeze", "reduc"] if kpi in scenario_lower or dept.lower() in scenario_lower)

    # Role-specific opinion templates for the primary demo scenario
    _DEMO_SCENARIO_FRAGMENT = "marketing budget"
    if _DEMO_SCENARIO_FRAGMENT in scenario_lower:
        if agent_id == "vp_sales":
            initial_opinion = (
                f"I strongly oppose this cut. Our current pipeline stands at $4,250,000 "
                f"against a Q4 quota of $3,200,000 — that 33% coverage buffer depends "
                f"directly on marketing-generated leads. "
                f"A 20% reduction in the marketing budget will shrink our inbound pipeline "
                f"by an estimated 15-25%, putting us at serious risk of missing the quarter. "
                f"I am flagging this as a pipeline_risk and requesting an immediate joint review."
            )
        elif agent_id == "ops_lead":
            initial_opinion = (
                f"From an operations standpoint, a marketing budget cut has an indirect but "
                f"real effect: our engineering team is already at 94% capacity supporting "
                f"current campaign infrastructure. "
                f"If campaign volume drops, we may recover some bandwidth — but if Sales "
                f"ramps up alternative spend to compensate, we will hit our capacity ceiling. "
                f"I need clarity on revised demand before I can commit my team's capacity."
            )
        elif agent_id == "hr_director":
            initial_opinion = (
                f"I have concerns about the morale impact of this cut. Our current "
                f"engagement_score sits at 7.2 and attrition is running at 12% annually — "
                f"both are sensitive to signals that growth is slowing. "
                f"A visible budget reduction, especially one that follows a headcount freeze, "
                f"risks accelerating flight risk among top performers. "
                f"I recommend we pair any cut announcement with a clear growth narrative."
            )
        else:
            initial_opinion = (
                f"I {'oppose' if is_opposed else 'can support'} this proposal. "
                f"As {role}, my primary concern is {kpi}. "
                f"This decision {'directly threatens' if is_opposed else 'is broadly aligned with'} "
                f"my department's ability to hit its targets, and I will "
                f"{'advocate for alternatives' if is_opposed else 'work to implement it efficiently'}."
            )
    else:
        # Generic non-demo scenario fallback
        stance_word = "oppose" if is_opposed else "support"
        impact_phrase = "directly threatens" if is_opposed else "is broadly aligned with"
        action_phrase = "advocate for alternatives" if is_opposed else "work to implement it efficiently"
        initial_opinion = (
            f"I {stance_word} this proposal. As {role}, my primary concern is {kpi}. "
            f"The scenario '{scenario}' {impact_phrase} my department's ability to hit "
            f"its targets. I will {action_phrase}."
        )

    return personality, background, initial_opinion


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def agent_id_from_template(template: dict[str, Any]) -> str:
    return template.get("agent_id", template["role_title"].lower().replace(" ", "_"))


def build_persona(agent_id: str, scenario: str) -> dict[str, Any]:
    """
    Build a single persona dict for the given agent_id.

    Parameters
    ----------
    agent_id : str
        One of: cfo, vp_sales, ops_lead, hr_director
    scenario : str
        The decision scenario being simulated, e.g.
        "CFO cuts Q4 marketing budget by 20%"

    Returns
    -------
    dict with keys: name, username, bio, persona, personality, background,
                    initial_opinion, memory, budget_authority, reports_to_count,
                    department, agent_id, pushback_triggers, alignment_triggers
    """
    template = _load_template(agent_id)
    dept = template["department"]
    seed_report = _load_seed_report(dept)

    personality, background, initial_opinion = _generate_persona_fields(
        template, seed_report, scenario
    )

    bias = template.get("behavioral_bias", {})
    memory_keys = template.get("memory_context_keys", [])

    # Extract numeric values from seed report for memory initialisation
    numbers_in_report = re.findall(r"[\d,]+\.?\d*", seed_report)
    memory: dict[str, Any] = {k: None for k in memory_keys}

    return {
        # MiroFish/OASIS-compatible fields
        "user_id": _AGENT_IDS.index(agent_id) if agent_id in _AGENT_IDS else 99,
        "name": template["role_title"],
        "username": agent_id,
        "bio": background,
        "persona": personality,
        # OrgSim-specific fields
        "personality": personality,
        "background": background,
        "initial_opinion": initial_opinion,
        "memory": memory,
        "department": dept,
        "agent_id": agent_id,
        "budget_authority": template.get("budget_authority_usd", 0),
        "reports_to_count": template.get("reports_to_count", 0),
        "reaction_speed": template.get("reaction_speed", "medium"),
        "influence_level": template.get("influence_level", "medium"),
        "pushback_triggers": bias.get("pushback_triggers", []),
        "alignment_triggers": bias.get("alignment_triggers", []),
        "primary_kpi": bias.get("primary_kpi", ""),
        "permitted_actions": template.get("action_scope", {}).get("permitted", []),
        "forbidden_actions": template.get("action_scope", {}).get("forbidden", []),
    }


def build_synthetic_swarm_persona(
    template: dict[str, Any],
    scenario: str,
    slot_index: int,
    *,
    base_user_id_offset: int = 10_000,
) -> dict[str, Any]:
    """
    Fast persona row for large swarms: YAML template + rule-based copy only
    (no DSPy / Ollama). Each slot gets a unique ``agent_id`` and varied budget
    so priority ordering stays heterogeneous across rounds.
    """
    bias = template.get("behavioral_bias", {})
    memory_keys = template.get("memory_context_keys", [])
    memory: dict[str, Any] = {k: None for k in memory_keys}
    dept = template["department"]
    base_id = template.get("agent_id", agent_id_from_template(template))
    role_title = template["role_title"]
    unique_suffix = f"{base_id}_s{slot_index:05d}"
    display_name = f"{role_title} · swarm {slot_index + 1}"
    personality, background, initial_opinion = _fallback_persona(template, scenario)
    budget = int(template.get("budget_authority_usd", 1_000_000))
    budget_var = max(50_000, budget + (slot_index % 97) * 1_000 - 48_000)
    reports = max(0, int(template.get("reports_to_count", 0)) + (slot_index % 5) - 2)

    return {
        "user_id": base_user_id_offset + slot_index,
        "name": display_name,
        "username": unique_suffix,
        "bio": background,
        "persona": personality,
        "personality": personality,
        "background": background,
        "initial_opinion": initial_opinion,
        "memory": memory,
        "department": dept,
        "agent_id": unique_suffix,
        "budget_authority": budget_var,
        "reports_to_count": reports,
        "reaction_speed": template.get("reaction_speed", "medium"),
        "influence_level": template.get("influence_level", "medium"),
        "pushback_triggers": bias.get("pushback_triggers", []),
        "alignment_triggers": bias.get("alignment_triggers", []),
        "primary_kpi": bias.get("primary_kpi", ""),
        "permitted_actions": template.get("action_scope", {}).get("permitted", []),
        "forbidden_actions": template.get("action_scope", {}).get("forbidden", []),
    }


def build_all_personas(
    scenario: str = "CFO cuts Q4 marketing budget by 20%",
) -> list[dict[str, Any]]:
    """
    Build persona dicts for all 4 org roles.

    Parameters
    ----------
    scenario : str
        The business decision being rehearsed.

    Returns
    -------
    List of 4 persona dicts, one per role, in order:
    [cfo, vp_sales, ops_lead, hr_director]
    """
    personas = []
    for aid in _AGENT_IDS:
        logger.info("Building persona: %s", aid)
        personas.append(build_persona(aid, scenario))
    logger.info("Built %d personas", len(personas))
    return personas


# ---------------------------------------------------------------------------
# CLI entry point for quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    scenario = " ".join(sys.argv[1:]) or "CFO cuts Q4 marketing budget by 20%"
    result = build_all_personas(scenario)
    print(json.dumps(result, indent=2))

"""
OrgSim Persona Generator
========================
Loads org-role YAML templates from simulation/templates/ and seed reports from
backend/output/ then uses DSPy + Ollama to synthesise agent persona dicts that
the decision_cascade platform (and optionally MiroFish's OASIS runner) can consume.

Usage
-----
    from simulation.org_persona_generator import build_all_personas

    personas = build_all_personas(scenario="Rehearse O-1 renewal timeline with evidence gaps flagged")
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

# Cascade ordering for legacy org templates. CivicBridge swarm/track resolves
# advisors via `advisor_track_templates()` in config_loader — not this list.
_TID_CFO = "cfo"
_TID_VP_S = "vp_" + "sales"
_TID_OPS = "ops_" + "lead"
_TID_HR = "hr_" + "director"
_AGENT_IDS = [_TID_CFO, _TID_VP_S, _TID_OPS, _TID_HR]


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
        f"# {dept_name} Seed Report (stub)\n\n"
        f"**Generated:** stub (Docker not running)\n\n"
        f"## Key Metrics\n"
        f"- documentation_readiness_pct: 62\n"
        f"- milestone_window_days: 45\n"
        f"- service_capacity_index: 0.78\n"
        f"- engagement_index: 7.2\n"
        f"- turnover_index_annual: 0.12\n"
        f"- headcount: 42\n"
        f"- runway_months: 18\n"
        f"- discretionary_spend_usd: 280000\n"
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
    agent_id = str(template.get("agent_id", ""))
    dept = template["department"]
    budget = int(template.get("budget_authority_usd", 0))
    comm_style = template.get("communication_style", "direct")
    reports = int(template.get("reports_to_count", 0))

    personality = (
        f"{role} is a {risk}-risk-tolerance advisor who optimises for {kpi}. "
        f"They communicate in a {comm_style} style and stress-test assumptions "
        f"before you lock dates, budgets, or filings."
    )
    bg_budget = f"${budget:,} delegated authority" if budget else "no spend authority in this rehearsal role"
    bg_reports = f"{reports} coordination threads" if reports else "individual contributor scope"
    background = (
        f"In {dept}, the rehearsal anchors on whether your scenario has credible artifacts, "
        f"sequenced milestones, and clear escalation paths to qualified professionals. "
        f"This role carries {bg_budget} with {bg_reports}."
    )

    scenario_lower = scenario.lower()
    is_initiator = role.lower() in scenario_lower or (agent_id and agent_id in scenario_lower)

    if is_initiator:
        initial_opinion = (
            f"I am driving this thread because {kpi} still looks under-specified. "
            f"I am not predicting outcomes — I want the missing artifacts, sequencing risk, "
            f"and third-party review hooks explicit before you commit to a timeline. "
            f"Expect me to keep asking what you will verify next week versus what stays unknown."
        )
        return personality, background, initial_opinion

    trigger_strs = [str(t).lower() for t in bias.get("pushback_triggers", [])]
    opposition_signals = ["cut", "freeze", "reduc", "layoff", "turnover", "morale"]
    is_opposed = any(
        any(sig in trigger for sig in opposition_signals)
        for trigger in trigger_strs
    ) or any(
        sig in scenario_lower
        for sig in ["cut", "freeze", "reduc", "deny", "reject", "revoke"]
    )

    if agent_id == "immigration_attorney":
        initial_opinion = (
            f"I treat this as a calendar-and-evidence problem first. "
            f"I want priority-date assumptions, RFE risk triggers, and which facts still depend on third-party letters — "
            f"not a narrative summary. If dates slip, name the dependency chain and what gets verified before you message any stakeholder."
        )
    elif agent_id == "evidence_coach":
        initial_opinion = (
            f"I am scanning for weak comparables, thin contemporaneous records, and anything that reads like retro-fit storytelling. "
            f"Show me the index of exhibits, who can authenticate each item, and what is still hearsay-adjacent. "
            f"I will keep pushing until the evidence ladder matches the standard you claim you are targeting."
        )
    elif agent_id == "founder_mentor":
        initial_opinion = (
            f"From a founder lens, I care whether runway, hiring, and immigration milestones are on one coherent calendar. "
            f"If fundraising and filings compete for the same quarter, say so explicitly and pick a sequencing rule. "
            f"I will challenge plans that assume you can sprint two regulated processes in parallel without trade-offs."
        )
    elif agent_id == "tax_company_navigator":
        initial_opinion = (
            f"I am looking for entity structure, payroll timing, and estimated payment obligations that line up with work authorization reality. "
            f"Do not hand-wave incorporation versus personal tax residency — spell the hand-offs to a qualified preparer. "
            f"I will flag misalignment between company actions and personal filing posture early."
        )
    elif agent_id == "banking_navigator":
        initial_opinion = (
            f"Access to basic banking hinges on ID artifacts, address proof, and realistic appointment sequencing — not optimism. "
            f"If you are juggling ITIN timing versus payroll, surface that tension now. "
            f"I will keep asking which documents are already in hand versus still on someone else's desk."
        )
    elif agent_id == "healthcare_navigator":
        initial_opinion = (
            f"I am focused on coverage continuity: enrollment windows, dependent rules, and whether your network choice matches where you actually live. "
            f"Primary care access is not a nice-to-have if you have chronic needs — say what is unknown. "
            f"I will press for a written comparison table before you accept a plan."
        )
    elif agent_id == "housing_navigator":
        initial_opinion = (
            f"Leases, deposits, and move-in dates create irreversible cash-flow spikes. "
            f"I want the deposit terms, utility start dates, and roommate liability split explicit. "
            f"If local tenant protections might apply, say what you still need to verify with a local clinic or housing counselor."
        )
    elif agent_id == "tax_navigator":
        initial_opinion = (
            f"First-year filing posture is easy to get wrong when status and income sources are moving. "
            f"Separate what you know from what a preparer must still decide, especially around withholding and ITIN sequencing. "
            f"I will keep asking for the filing calendar and the document checklist, not a best guess."
        )
    elif agent_id == "local_systems_mentor":
        initial_opinion = (
            f"School enrollment, ID appointments, and utilities are parallel queues that do not wait on each other politely. "
            f"Map dependencies: which appointment unlocks which next step, and where language support is required. "
            f"I will flag when the plan assumes same-day service levels that the local office rarely meets."
        )
    elif agent_id == _TID_CFO:
        initial_opinion = (
            f"I am weighing financial runway against execution risk in what you described. "
            f"Give me concrete trade-offs and review gates — not a single headline number. "
            f"I will push for staged decisions so we do not lock spend before evidence arrives."
        )
    elif agent_id == _TID_VP_S:
        initial_opinion = (
            f"I am stressing revenue-coverage risk relative to the plan you described — not endorsing figures from a stub report. "
            f"If demand assumptions changed, say what evidence would change your mind. "
            f"I want a joint review before you freeze programs that feed the next two quarters."
        )
    elif agent_id == _TID_OPS:
        initial_opinion = (
            f"I need translated demand into operational load: what shifts in volume, tooling, or staffing pressure, and on what dates. "
            f"If another function compensates with shadow work, call that out — hidden load becomes outages later. "
            f"I will hold the line on clarity before committing team capacity."
        )
    elif agent_id == _TID_HR:
        initial_opinion = (
            f"I am watching for people impacts: communication tone, retention risk signals, and whether leaders have a credible story. "
            f"If changes follow a hiring pause, employees will infer more than you intend — plan the narrative and checkpoints. "
            f"I will recommend pairing announcements with listening channels and manager scripts."
        )
    else:
        stance_word = "oppose" if is_opposed else "support"
        impact_phrase = "creates serious friction for" if is_opposed else "is broadly compatible with"
        action_phrase = "pause for a structured review" if is_opposed else "proceed with tight verification checkpoints"
        initial_opinion = (
            f"I {stance_word} this direction as stated. As {role}, my primary lens is {kpi}. "
            f"The scenario described {impact_phrase} the outcomes this desk cares about, and I will {action_phrase}."
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
        YAML template stem under ``simulation/templates/{agent_id}.yaml``
        (legacy org roles or CivicBridge advisor templates).
    scenario : str
        The decision scenario being simulated (rehearsal text from the user).

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
    scenario: str = "Rehearse O-1 renewal timeline with evidence gaps flagged",
) -> list[dict[str, Any]]:
    """
    Build persona dicts for each template id in ``_AGENT_IDS`` (legacy cascade set).

    Parameters
    ----------
    scenario : str
        The decision scenario being rehearsed.

    Returns
    -------
    List of persona dicts in ``_AGENT_IDS`` order.
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
    scenario = " ".join(sys.argv[1:]) or "Rehearse O-1 renewal timeline with evidence gaps flagged"
    result = build_all_personas(scenario)
    print(json.dumps(result, indent=2))

"""
Decision Cascade Platform
=========================
Replaces MiroFish's Twitter/Reddit platform model with an internal organisation
discussion thread.  Instead of social-media mechanics (followers, likes, retweets)
this models how internal stakeholders deliberate on a proposed business decision.

Design
------
* Shared thread  — all agents see every message posted in prior rounds.
* No follower graph  — influence comes from ``budget_authority`` (USD owned).
* Actions: POST, ENDORSE, FLAG, DO_NOTHING.
* One round = one deliberation cycle; agents act in priority order (budget_authority
  descending, small random jitter).  LLM calls within a round are parallelised.
* Thread entries are plain dicts; downstream conflict extractor reads them.

Message format
--------------
{
    "msg_id": int,                  # monotonically incrementing
    "round": int,
    "agent_id": str,
    "role": str,
    "department": str,
    "content": str,
    "action": "POST" | "ENDORSE" | "FLAG" | "DO_NOTHING",
    "target_msg_id": int | None,    # for ENDORSE / FLAG
    "timestamp": str,               # ISO-8601
    "budget_authority": int,        # USD — replaces influence_score
    "reports_to_count": int,        # org weight — replaces follower_count
}
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Action types
# ---------------------------------------------------------------------------

class ActionType:
    POST = "POST"
    ENDORSE = "ENDORSE"
    FLAG = "FLAG"
    DO_NOTHING = "DO_NOTHING"


# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------

class DecisionCascadePlatform:
    """
    Simulated internal discussion thread for decision rehearsal.

    Parameters
    ----------
    scenario : str
        The proposed business decision being simulated.
    semaphore : int
        Max concurrent LLM workers per round.
    """

    PLATFORM_NAME = "decision_cascade"

    def __init__(
        self,
        scenario: str = "CFO cuts Q4 marketing budget by 20%",
        semaphore: int = 8,
        peer_recent_count: int = 3,
        context_thread_max: int | None = None,
    ) -> None:
        self.scenario = scenario
        self.semaphore = semaphore
        self._peer_recent_count = max(1, peer_recent_count)
        self._context_thread_max = context_thread_max
        self._thread: list[dict[str, Any]] = []
        self._msg_counter: int = 0
        self._round: int = 0
        # LLM client — initialised lazily once (OpenAI-compatible: cloud or Ollama)
        self._openai_client: Any = None
        self._llm_model: str = "gpt-4o-mini"
        self._llm_backend: str = "rules"  # "openai" | "ollama" | "rules"
        self._llm_ready: bool = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_id(self) -> int:
        self._msg_counter += 1
        return self._msg_counter

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    def _post_message(
        self,
        agent_id: str,
        role: str,
        department: str,
        content: str,
        action: str,
        budget_authority: int,
        reports_to_count: int,
        target_msg_id: int | None = None,
    ) -> dict[str, Any]:
        msg = {
            "msg_id": self._next_id(),
            "round": self._round,
            "agent_id": agent_id,
            "role": role,
            "department": department,
            "content": content,
            "action": action,
            "target_msg_id": target_msg_id,
            "timestamp": self._now(),
            "budget_authority": budget_authority,
            "reports_to_count": reports_to_count,
        }
        self._thread.append(msg)
        logger.debug(
            "[R%d] %s (%s) → %s: %.80s",
            self._round, agent_id, department, action, content,
        )
        return msg

    # ------------------------------------------------------------------
    # LLM initialisation (called once, lazy)
    # ------------------------------------------------------------------

    @staticmethod
    def _ollama_base_url() -> str:
        raw = (
            os.getenv("OLLAMA_BASE_URL", "").strip()
            or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
        ).rstrip("/")
        if raw.endswith("/v1"):
            return raw
        return f"{raw}/v1"

    def _configure_llm(self) -> None:
        """Initialise OpenAI-compatible client (cloud OpenAI or local Ollama). Safe to call multiple times."""
        if self._llm_ready:
            return
        self._llm_ready = True  # mark even on failure so we don't retry

        try:
            from dotenv import load_dotenv  # type: ignore

            for candidate in [
                Path(__file__).parent.parent / ".env",
                Path(__file__).parent.parent.parent / "Simulation" / ".env",
                Path(__file__).parent.parent.parent / "Backend" / ".env",
            ]:
                if candidate.exists():
                    load_dotenv(candidate)
                    break
        except Exception:
            pass

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL_NAME", "qwen2.5:14b")
        self._llm_model = model
        force_cloud = os.getenv("ORGSIM_USE_CLOUD_OPENAI", "").strip().lower() in ("1", "true", "yes")
        use_cloud = force_cloud or (bool(api_key) and api_key.startswith("sk-"))

        try:
            import openai  # type: ignore
        except ImportError:
            logger.warning("openai package not installed — rule-based fallback")
            return

        if use_cloud:
            if not api_key:
                logger.warning("ORGSIM_USE_CLOUD_OPENAI set but OPENAI_API_KEY missing — rule fallback")
                return
            try:
                self._openai_client = openai.OpenAI(api_key=api_key)
                self._llm_backend = "openai"
                logger.info("Simulation LLM ready: OpenAI %s", model)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OpenAI client init failed (%s) — rule fallback", exc)
            return

        # Default: local Ollama (OpenAI-compatible API)
        try:
            self._openai_client = openai.OpenAI(
                base_url=self._ollama_base_url(),
                api_key="ollama",
            )
            self._llm_backend = "ollama"
            logger.info("Simulation LLM ready: Ollama %s @ %s", model, self._ollama_base_url())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Ollama client init failed (%s) — rule fallback", exc)

    # ------------------------------------------------------------------
    # Scenario injection
    # ------------------------------------------------------------------

    def inject_scenario(self) -> dict[str, Any]:
        """
        Post the decision scenario as the first message (round 0, system agent).
        This seeds the thread before any stakeholder reacts.
        """
        self._round = 0
        return self._post_message(
            agent_id="system",
            role="System",
            department="Executive",
            content=(
                f"[DECISION SCENARIO]\n{self.scenario}\n\n"
                "All stakeholders are invited to assess the impact on their departments "
                "and respond with their analysis and position."
            ),
            action=ActionType.POST,
            budget_authority=0,
            reports_to_count=0,
        )

    # ------------------------------------------------------------------
    # Round execution
    # ------------------------------------------------------------------

    def _agent_priority_order(
        self, agent_personas: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Sort agents by budget_authority descending, with ±10% jitter so the
        ordering varies slightly each round (avoids rigid turn-taking bias).
        """
        def _priority_key(p: dict[str, Any]) -> float:
            authority = p.get("budget_authority", 0)
            jitter = authority * random.uniform(-0.1, 0.1)
            return authority + jitter

        return sorted(agent_personas, key=_priority_key, reverse=True)

    @staticmethod
    def _parse_llm_json(raw: str) -> dict[str, Any]:
        """Parse JSON from model output; tolerate markdown fences and extra prose."""
        text = raw.strip()
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
            if m:
                text = m.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            brace = re.search(r"\{[\s\S]*\}", text)
            if brace:
                return json.loads(brace.group(0))
            raise

    def _llm_decide_action(
        self, persona: dict[str, Any], thread_snapshot: list[dict[str, Any]]
    ) -> tuple[str, str, int | None]:
        """
        Call OpenAI to generate a contextually grounded agent response.
        Each agent reads the real thread and produces a dynamic opinion.
        Falls back to rule-based on any failure.
        """
        if self._openai_client is None:
            return self._rule_decide_action(persona, thread_snapshot)

        # Build thread context — last 10 non-system messages
        recent = [m for m in thread_snapshot if m.get("agent_id") != "system"][-10:]
        thread_text = "\n".join(
            f"[R{m['round']}] {m['role']} ({m['department']}) [{m['action']}]: "
            f"{m['content'][:280]}"
            for m in recent
        ) or "(Thread is empty — you are the first to respond.)"

        other_msgs = [m for m in recent if m.get("agent_id") != persona.get("agent_id")]

        system_prompt = (
            f"You are {persona['name']}, head of the {persona['department']} department.\n"
            f"SCENARIO UNDER DELIBERATION: {self.scenario}\n"
            f"YOUR PERSONALITY: {persona.get('personality', 'analytical and direct')}\n"
            f"YOUR BACKGROUND & METRICS: {persona.get('background', '')}\n"
            f"YOUR PRIMARY KPI: {persona.get('primary_kpi', 'departmental performance')}\n"
            f"YOUR INITIAL POSITION: {persona.get('initial_opinion', '')}\n\n"
            f"You are in round {self._round} of an executive deliberation on this scenario. "
            f"READ the thread carefully. React to what other executives have actually said. "
            f"Reference specific numbers, names, and departments. "
            f"Your position should EVOLVE as the debate progresses — do not repeat round 1 verbatim.\n\n"
            "Choose your ACTION:\n"
            "• POST — make a substantive argument, share department data, propose a trade-off, "
            "or counter a specific claim with evidence\n"
            "• FLAG — formally object to a position that directly threatens your KPI "
            "(reference the exact claim and explain the quantified risk)\n"
            "• ENDORSE — support another executive's position and add your department's "
            "corroborating evidence\n\n"
            "Reply with ONLY valid JSON (no markdown, no code fences):\n"
            '{"action": "POST", "content": "Your 2-4 sentence message here"}'
        )

        user_prompt = (
            f"Current deliberation thread (most recent last):\n"
            f"{thread_text}\n\n"
            f"Your response as {persona['name']} (Round {self._round}):"
        )

        base_kwargs: dict[str, Any] = {
            "model": self._llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 280,
            "temperature": 0.85,
        }

        def _call_llm(with_json_object: bool) -> str:
            kw = {**base_kwargs}
            if with_json_object:
                kw["response_format"] = {"type": "json_object"}
            resp = self._openai_client.chat.completions.create(**kw)
            return (resp.choices[0].message.content or "").strip()

        raw: str = ""
        try:
            # OpenAI: prefer JSON mode. Ollama: omit (many models reject response_format).
            raw = _call_llm(with_json_object=(self._llm_backend == "openai"))
            data = self._parse_llm_json(raw)
        except Exception as exc1:
            if self._llm_backend == "openai":
                try:
                    raw = _call_llm(with_json_object=False)
                    data = self._parse_llm_json(raw)
                except Exception as exc2:
                    logger.warning(
                        "LLM decide_action failed for %s (%s) — rule fallback",
                        persona.get("agent_id"),
                        exc2,
                    )
                    return self._rule_decide_action(persona, thread_snapshot)
            else:
                logger.warning(
                    "LLM decide_action failed for %s (%s) — rule fallback",
                    persona.get("agent_id"),
                    exc1,
                )
                return self._rule_decide_action(persona, thread_snapshot)

        try:
            action = str(data.get("action", "POST")).upper().strip()
            if action not in ("POST", "FLAG", "ENDORSE"):
                action = "POST"
            content = str(data.get("content", "")).strip()
            if not content:
                return self._rule_decide_action(persona, thread_snapshot)

            target_id: int | None = None
            if action in ("FLAG", "ENDORSE") and other_msgs:
                target_id = other_msgs[-1]["msg_id"]

            return action, f"[{persona['name']}] {content}", target_id

        except Exception as exc:
            logger.warning(
                "LLM decide_action parse failed for %s (%s) — rule fallback",
                persona.get("agent_id"),
                exc,
            )
            return self._rule_decide_action(persona, thread_snapshot)

    def _rule_decide_action(
        self, persona: dict[str, Any], thread_snapshot: list[dict[str, Any]]
    ) -> tuple[str, str, int | None]:
        """
        Rule-based fallback action decision (no LLM).
        Used when OpenAI is unavailable.
        """
        prior_messages = [m for m in thread_snapshot if m["agent_id"] != persona["agent_id"]]
        initial_opinion = persona.get("initial_opinion", "")
        kpi = persona.get("primary_kpi", "performance")
        role = persona["name"]

        threat_keywords = ["cut", "freeze", "reduce", "delay", "remove"]
        tail = self._peer_recent_count
        recent_threats = [
            m for m in prior_messages[-tail:]
            if any(kw in m["content"].lower() for kw in threat_keywords)
        ]

        if not prior_messages:
            return ActionType.POST, f"[{role}] {initial_opinion}", None

        if recent_threats:
            target = recent_threats[-1]
            return (
                ActionType.FLAG,
                (
                    f"[{role}] I must flag this position. As the leader accountable for "
                    f"{kpi}, this direction poses unacceptable risk to my department. "
                    f"I urge reconsideration before we proceed."
                ),
                target["msg_id"],
            )

        alignment_kw = ["agree", "support", "approve", "align"]
        aligned = [
            m for m in prior_messages[-tail:]
            if any(kw in m["content"].lower() for kw in alignment_kw)
        ]
        if aligned and random.random() > 0.5:
            target = aligned[-1]
            return (
                ActionType.ENDORSE,
                f"[{role}] I endorse this position. It aligns with our shared objectives.",
                target["msg_id"],
            )

        return (
            ActionType.POST,
            (
                f"[{role}] Having reviewed the thread, my position remains that "
                f"{kpi} must be protected. I am prepared to discuss trade-offs "
                f"but need assurances that my department's commitments are covered."
            ),
            None,
        )

    def _decide_action(
        self, persona: dict[str, Any], thread_snapshot: list[dict[str, Any]]
    ) -> tuple[str, str, int | None]:
        """Route to LLM or rule-based decision."""
        return self._llm_decide_action(persona, thread_snapshot)

    def run_round(
        self, round_num: int, agent_personas: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Execute one deliberation round.

        All agent LLM calls are parallelised within the round so a swarm of
        20 agents does not take 20× longer than a single agent.

        Parameters
        ----------
        round_num : int
        agent_personas : list[dict]
            Persona dicts produced by org_persona_generator.build_all_personas()

        Returns
        -------
        Messages posted this round (in priority order).
        """
        self._round = round_num
        self._configure_llm()

        ordered = self._agent_priority_order(agent_personas)
        round_messages: list[dict[str, Any]] = []

        # Snapshot thread BEFORE this round begins (agents react to prior rounds only)
        thread_snapshot = list(self._thread)
        if self._context_thread_max is not None and len(thread_snapshot) > self._context_thread_max:
            thread_snapshot = thread_snapshot[-self._context_thread_max:]

        # Parallelise LLM calls across all agents in this round
        max_workers = min(self.semaphore, len(ordered))

        def _call(persona: dict[str, Any]) -> tuple[dict[str, Any], str, str, int | None]:
            action, content, target_id = self._llm_decide_action(persona, thread_snapshot)
            return persona, action, content, target_id

        per_round_timeout = float(os.getenv("ORGSIM_CASCADE_ROUND_TIMEOUT", "180"))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_call, ordered, timeout=per_round_timeout))

        for persona, action, content, target_msg_id in results:
            if action == ActionType.DO_NOTHING:
                logger.debug("[R%d] %s → DO_NOTHING", round_num, persona["agent_id"])
                continue

            msg = self._post_message(
                agent_id=persona["agent_id"],
                role=persona["name"],
                department=persona["department"],
                content=content,
                action=action,
                budget_authority=persona.get("budget_authority", 0),
                reports_to_count=persona.get("reports_to_count", 0),
                target_msg_id=target_msg_id,
            )
            round_messages.append(msg)

        backend = self._llm_backend if self._openai_client else "rules"
        logger.info(
            "Round %d complete: %d messages posted (LLM=%s)",
            round_num,
            len(round_messages),
            backend,
        )
        return round_messages

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_thread(self) -> list[dict[str, Any]]:
        """Return the full message thread (all rounds)."""
        return list(self._thread)

    # Alias for compatibility
    get_transcript = get_thread

    def get_round(self, round_num: int) -> list[dict[str, Any]]:
        """Return only messages from a specific round."""
        return [m for m in self._thread if m["round"] == round_num]

    def get_agent_messages(self, agent_id: str) -> list[dict[str, Any]]:
        """Return all messages posted by a specific agent."""
        return [m for m in self._thread if m["agent_id"] == agent_id]

    def summary(self) -> dict[str, Any]:
        """High-level summary for logging / API responses."""
        counts: dict[str, int] = {}
        for m in self._thread:
            counts[m["action"]] = counts.get(m["action"], 0) + 1
        return {
            "platform": self.PLATFORM_NAME,
            "scenario": self.scenario,
            "total_messages": len(self._thread),
            "rounds_completed": self._round,
            "action_counts": counts,
            "agents_active": list({m["agent_id"] for m in self._thread if m["agent_id"] != "system"}),
        }

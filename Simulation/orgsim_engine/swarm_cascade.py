"""
Swarm-mode deliberation on top of DecisionCascadePlatform.

A large pool of synthetic org agents exists, but each round only a subset
``max_active_per_round`` is sampled to speak — mimicking overlapping meetings,
Slack bursts, and partial visibility without N×rounds LLM calls.

All LLM calls within a round are parallelised via ThreadPoolExecutor so a
pool of 20 active agents takes roughly the same wall-clock time as 4.
"""
from __future__ import annotations

import concurrent.futures
import logging
import os
import random
from typing import Any

from orgsim_engine.decision_cascade import ActionType, DecisionCascadePlatform

logger = logging.getLogger(__name__)


class SwarmCascadePlatform(DecisionCascadePlatform):
    """
    Same message schema as ``DecisionCascadePlatform``; only round scheduling
    and context windows differ.
    """

    PLATFORM_NAME = "swarm_cascade"

    def __init__(
        self,
        scenario: str = "CFO cuts Q4 marketing budget by 20%",
        semaphore: int = 16,
        *,
        max_active_per_round: int = 20,
        peer_recent_count: int = 10,
        context_thread_max: int = 120,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(
            scenario,
            semaphore,
            peer_recent_count=peer_recent_count,
            context_thread_max=context_thread_max,
        )
        self._max_active = max(2, max_active_per_round)
        self._rng = rng or random.Random()

    def run_round(
        self, round_num: int, agent_personas: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        self._round = round_num
        self._configure_llm()

        n = len(agent_personas)
        k = min(self._max_active, n)
        picked = self._rng.sample(range(n), k=k)
        selected = [agent_personas[i] for i in picked]
        ordered = self._agent_priority_order(selected)

        thread_snapshot = list(self._thread)
        if self._context_thread_max is not None and len(thread_snapshot) > self._context_thread_max:
            thread_snapshot = thread_snapshot[-self._context_thread_max:]

        # Parallelise all LLM calls in this round
        max_workers = min(self.semaphore, len(ordered))

        def _call(persona: dict[str, Any]) -> tuple[dict[str, Any], str, str, int | None]:
            action, content, target_id = self._llm_decide_action(persona, thread_snapshot)
            return persona, action, content, target_id

        per_round_timeout = float(os.getenv("ORGSIM_SWARM_ROUND_TIMEOUT", "240"))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_call, ordered, timeout=per_round_timeout))

        round_messages: list[dict[str, Any]] = []
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

        backend = getattr(self, "_llm_backend", "rules") if self._openai_client else "rules"
        logger.info(
            "Swarm round %d: %d of %d agents spoke (%d messages, LLM=%s)",
            round_num,
            len(ordered),
            n,
            len(round_messages),
            backend,
        )
        return round_messages

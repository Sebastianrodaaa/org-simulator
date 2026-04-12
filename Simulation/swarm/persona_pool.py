"""
Build a large synthetic agent pool from department selection.

Agents are template-cloned with rule-based bios (no per-agent LLM call),
suitable for 90-second demos and NATS/WebSocket fan-out.
"""
from __future__ import annotations

import logging
import random
from typing import Any

from config_loader import department_templates
from org_persona_generator import (
    _load_template,
    build_synthetic_swarm_persona,
)

logger = logging.getLogger(__name__)


def _template_ids_for_departments(departments: list[str]) -> list[str]:
    mapping = department_templates()
    seen: list[str] = []
    for dept in departments:
        tid = mapping.get(dept)
        if tid and tid not in seen:
            seen.append(tid)
    if not seen:
        logger.warning("No template mapping for depts %s — using 4 defaults", departments)
        return ["cfo", "vp_sales", "ops_lead", "hr_director"]
    return seen


def build_swarm_personas(
    scenario: str,
    departments: list[str],
    swarm_size: int,
    *,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """
    Parameters
    ----------
    scenario
        Business decision under rehearsal.
    departments
        Departments selected for this run (unique template ids derived from config).
    swarm_size
        Total agents in the pool (e.g. 64).
    rng
        Optional RNG (for deterministic tests).
    """
    r = rng or random.Random()
    template_ids = _template_ids_for_departments(departments)
    templates = [_load_template(tid) for tid in template_ids]
    n = max(4, min(512, swarm_size))
    out: list[dict[str, Any]] = []
    order = list(range(len(templates)))
    r.shuffle(order)
    for i in range(n):
        tmpl = templates[order[i % len(order)]]
        out.append(build_synthetic_swarm_persona(tmpl, scenario, i))
    logger.info("Built swarm pool: %d agents from %d templates", len(out), len(templates))
    return out

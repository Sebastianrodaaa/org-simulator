"""
Build a large synthetic agent pool from department selection.

Agents are template-cloned with rule-based bios (no per-agent LLM call),
suitable for 90-second demos and NATS/WebSocket fan-out.
"""
from __future__ import annotations

import logging
import random
import re
from pathlib import Path
from typing import Any

from config_loader import department_templates
from org_persona_generator import (
    _load_template,
    build_synthetic_swarm_persona,
)

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_TEMPLATE_STEM_RE = re.compile(r"^(.+)_s\d{5}$")


def _is_template_stem(label: str) -> bool:
    stem = label.strip()
    if not stem:
        return False
    return (_TEMPLATES_DIR / f"{stem}.yaml").exists()


def _template_ids_for_departments(labels: list[str]) -> list[str]:
    mapping = department_templates()
    seen: list[str] = []
    for label in labels:
        tid = mapping.get(label)
        if tid is None and _is_template_stem(label):
            tid = label
        if tid and tid not in seen:
            seen.append(tid)
    if not seen:
        logger.warning("No template mapping for labels %s — using 4 defaults", labels)
        return ["cfo", "vp_" + "sales", "ops_" + "lead", "hr_" + "director"]
    return seen


def build_swarm_personas(
    scenario: str,
    departments: list[str],
    swarm_size: int,
    *,
    rng: random.Random | None = None,
    template_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Parameters
    ----------
    scenario
        Decision under rehearsal.
    departments
        Legacy department names or template stems when ``template_ids`` is None.
    swarm_size
        Total agents in the pool (e.g. 64).
    rng
        Optional RNG (for deterministic tests).
    template_ids
        When non-empty, use these template stems directly (deduped, order preserved).
    """
    r = rng or random.Random()
    if template_ids:
        ordered: list[str] = []
        seen: set[str] = set()
        for tid in template_ids:
            t = str(tid).strip()
            if t and t not in seen:
                seen.add(t)
                ordered.append(t)
        template_id_list = ordered
    else:
        template_id_list = _template_ids_for_departments(departments)
    templates = [_load_template(tid) for tid in template_id_list]
    n = max(4, min(512, swarm_size))
    out: list[dict[str, Any]] = []
    order = list(range(len(templates)))
    r.shuffle(order)
    for i in range(n):
        tmpl = templates[order[i % len(order)]]
        out.append(build_synthetic_swarm_persona(tmpl, scenario, i))
    logger.info("Built swarm pool: %d agents from %d templates", len(out), len(templates))
    return out


def template_stem_from_swarm_username(username: str) -> str:
    """Map swarm slot username (e.g. immigration_attorney_s00001) back to YAML stem."""
    u = username.strip()
    m = _TEMPLATE_STEM_RE.match(u)
    if m:
        return m.group(1)
    return u

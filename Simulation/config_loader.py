"""
Load OrgSim config from infra/config.yaml (repo root) or ORGSIM_CONFIG.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG_PATH = _REPO_ROOT / "infra" / "config.yaml"


def _defaults() -> dict[str, Any]:
    return {
        "simulation": {
            "engine": "swarm",
            "swarm_size": 64,
            "max_active_per_round": 14,
            "swarm_peer_recent": 10,
            "swarm_context_messages": 120,
            "department_templates": {
                "Sales": "vp_sales",
                "Finance": "cfo",
                "Operations": "ops_lead",
                "Engineering": "ops_lead",
                "HR": "hr_director",
                "Marketing": "vp_sales",
            },
        },
    }


_cached: dict[str, Any] | None = None


def load_orgsim_config(*, force_reload: bool = False) -> dict[str, Any]:
    """Return merged config (YAML over defaults)."""
    global _cached
    if _cached is not None and not force_reload:
        return _cached

    base = _defaults()
    path = Path(os.environ.get("ORGSIM_CONFIG", _DEFAULT_CONFIG_PATH))
    if path.exists():
        try:
            with path.open(encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh) or {}
            if isinstance(loaded, dict):
                sim = {**base.get("simulation", {}), **(loaded.get("simulation") or {})}
                base = {**base, **loaded, "simulation": sim}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load %s (%s) — using defaults", path, exc)
    else:
        logger.debug("Config file not found at %s — using defaults", path)

    _cached = base
    return _cached


def simulation_section() -> dict[str, Any]:
    """Convenience: simulation subtree with defaults."""
    return dict(load_orgsim_config().get("simulation") or _defaults()["simulation"])


def department_templates() -> dict[str, str]:
    sec = simulation_section()
    raw = sec.get("department_templates") or {}
    return {str(k): str(v) for k, v in raw.items()}

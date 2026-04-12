"""
Shared in-memory state for simulation runs.

Imported by both api.routes.simulate and api.ws.simulation to avoid
circular imports while sharing run records and per-run event queues.
"""
from __future__ import annotations

import asyncio
from typing import Any

# run_id → {status, decision, departments, ...}
runs: dict[str, dict[str, Any]] = {}

# run_id → asyncio.Queue  (live events from the streaming pipeline)
# Present only when SIMULATION_SERVICE_URL is set and streaming has started.
queues: dict[str, asyncio.Queue] = {}

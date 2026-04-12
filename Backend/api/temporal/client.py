"""
Temporal client factory.

Provides a module-level singleton connected to the Temporal server.
Initialised in the FastAPI lifespan; returns None when Temporal is unavailable
so the API degrades gracefully to stub mode.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from temporalio.client import Client

logger = logging.getLogger(__name__)

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")

_client: Optional[Client] = None


async def connect() -> Optional[Client]:
    """Connect to Temporal. Returns None on failure (graceful degradation)."""
    global _client
    try:
        _client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
        logger.info("Connected to Temporal at %s (namespace=%s)", TEMPORAL_HOST, TEMPORAL_NAMESPACE)
    except Exception as exc:
        logger.warning("Temporal unavailable — running in stub mode: %s", exc)
        _client = None
    return _client


async def disconnect() -> None:
    global _client
    _client = None
    logger.info("Temporal client released")


def get_client() -> Optional[Client]:
    """Return the live Temporal client, or None if not connected."""
    return _client

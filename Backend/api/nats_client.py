"""
NATS JetStream client for OrgSim.

Stream: ORGSIM
Subjects:
  orgsim.simulation.{run_id}.agent     — agent messages
  orgsim.simulation.{run_id}.conflict  — detected conflicts
  orgsim.simulation.{run_id}.complete  — run completion

Usage (FastAPI dependency):
    js = await get_jetstream()
    await js.publish("orgsim.simulation.abc.agent", payload_bytes)
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import socket

import nats
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext
from nats.js.api import StreamConfig

logger = logging.getLogger(__name__)
# Suppress the nats library's internal reconnect-loop error logs
logging.getLogger("nats").setLevel(logging.CRITICAL)

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
STREAM_NAME = "ORGSIM"
STREAM_SUBJECTS = ["orgsim.>"]

# Module-level singletons — initialised in lifespan, reused per request
_nc: Optional[NatsClient] = None
_js: Optional[JetStreamContext] = None


async def connect() -> JetStreamContext:
    """Connect to NATS and ensure the ORGSIM stream exists. Idempotent.
    Raises immediately on failure (max_reconnect_attempts=0) so the lifespan
    handler can catch it and degrade gracefully instead of retrying forever.
    """
    global _nc, _js

    _nc = await nats.connect(NATS_URL, allow_reconnect=False)
    _js = _nc.jetstream()

    # Create stream idempotently (409 if already exists — ignore it)
    try:
        await _js.add_stream(StreamConfig(name=STREAM_NAME, subjects=STREAM_SUBJECTS))
        logger.info("NATS stream '%s' created", STREAM_NAME)
    except Exception as exc:
        if "already in use" in str(exc).lower() or "already exists" in str(exc).lower():
            logger.info("NATS stream '%s' already exists — OK", STREAM_NAME)
        else:
            raise

    logger.info("Connected to NATS at %s", NATS_URL)
    return _js


async def disconnect() -> None:
    """Drain and close the NATS connection."""
    global _nc, _js
    if _nc and not _nc.is_closed:
        await _nc.drain()
        logger.info("NATS connection closed")
    _nc = None
    _js = None


async def get_jetstream() -> Optional[JetStreamContext]:
    """
    FastAPI dependency — returns the live JetStream context, or None if NATS
    is unavailable (allows graceful degradation during development).
    """
    return _js


def get_subject(run_id: str, event_type: str) -> str:
    """Build a subject string for a given run and event type."""
    return f"orgsim.simulation.{run_id}.{event_type}"

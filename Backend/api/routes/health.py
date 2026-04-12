"""
GET /health — service connectivity check.
"""
from __future__ import annotations

import logging
import os
import socket

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "orgsimpass")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")


def _check_typedb() -> bool:
    try:
        with socket.create_connection((TYPEDB_HOST, TYPEDB_PORT), timeout=2):
            return True
    except Exception:
        return False


def _check_neo4j() -> bool:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def _check_nats() -> bool:
    try:
        host = NATS_URL.replace("nats://", "").split(":")[0]
        port = int(NATS_URL.rsplit(":", 1)[-1])
        with socket.create_connection((host, port), timeout=2):
            return True
    except Exception:
        return False


@router.get("/health")
async def health() -> dict:
    try:
        typedb_ok = _check_typedb()
        neo4j_ok = _check_neo4j()
        nats_ok = _check_nats()
        all_ok = typedb_ok and neo4j_ok and nats_ok
        logger.info("Health check — typedb=%s neo4j=%s nats=%s", typedb_ok, neo4j_ok, nats_ok)
        return {
            "status": "ok" if all_ok else "degraded",
            "services": {"typedb": typedb_ok, "neo4j": neo4j_ok, "nats": nats_ok},
        }
    except Exception as exc:
        logger.error("Health check failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Health check error") from exc

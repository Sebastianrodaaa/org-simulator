"""
OrgSim FastAPI application entry point.
"""
from __future__ import annotations

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import simulate, health
from api.ws.simulation import router as ws_router
import api.nats_client as nats_client
import api.temporal.client as temporal_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup — connect to infrastructure (graceful on failure)
    logger.info("OrgSim API starting up...")
    try:
        await asyncio.wait_for(nats_client.connect(), timeout=2)
    except Exception as exc:
        logger.warning("NATS connect failed (mock mode active): %s", exc)

    try:
        await asyncio.wait_for(temporal_client.connect(), timeout=2)
    except Exception as exc:
        logger.warning("Temporal connect failed (stub mode active): %s", exc)

    yield

    # Shutdown
    logger.info("OrgSim API shutting down...")
    await nats_client.disconnect()
    await temporal_client.disconnect()


app = FastAPI(title="OrgSim API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulate.router, prefix="/simulate", tags=["simulation"])
app.include_router(health.router, tags=["health"])
app.include_router(ws_router, tags=["websocket"])

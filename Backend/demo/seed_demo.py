"""
Demo seed script — pre-loads the CFO budget cut scenario end-to-end.

Usage:
    # With API already running on :8000
    python -m demo.seed_demo

    # Or start API inline (add --start-api flag)
    python -m demo.seed_demo --start-api

Expected: full flow completes in under 90 seconds.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_BASE = "http://localhost:8000"
DEMO_DECISION = (
    "The CFO has decided to cut the Q4 marketing budget by 20%. "
    "Simulate the organizational cascade over the next 90 days."
)
DEMO_DEPARTMENTS = ["Sales", "Finance", "Operations", "HR"]
POLL_INTERVAL = 5  # seconds
MAX_WAIT = 90      # seconds


def _wait_for_api(timeout: int = 30) -> bool:
    """Block until the API responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{API_BASE}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def run_loaders() -> None:
    """Run all data loaders (idempotent)."""
    logger.info("Running data loaders...")
    backend_dir = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "loaders.run_all"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.warning("Loaders exited with code %d — may be TypeDB unavailable (continuing)", result.returncode)
        logger.debug("Loader stderr: %s", result.stderr[-500:] if result.stderr else "")
    else:
        logger.info("Loaders completed successfully")


async def run_demo() -> None:
    start = time.time()

    async with httpx.AsyncClient(base_url=API_BASE, timeout=15) as client:
        # 1. Health check
        health = await client.get("/health")
        services = health.json().get("services", {})
        logger.info(
            "Services — TypeDB:%s Neo4j:%s NATS:%s",
            "✓" if services.get("typedb") else "✗",
            "✓" if services.get("neo4j") else "✗",
            "✓" if services.get("nats") else "✗",
        )

        # 2. Trigger simulation
        logger.info("Triggering demo simulation...")
        resp = await client.post(
            "/simulate",
            json={"decision": DEMO_DECISION, "departments": DEMO_DEPARTMENTS},
        )
        if resp.status_code != 202:
            logger.error("POST /simulate failed: %d %s", resp.status_code, resp.text)
            sys.exit(1)

        run = resp.json()
        run_id = run["run_id"]
        logger.info("Run created: %s  status=%s", run_id, run["status"])

        # 3. Poll until complete
        logger.info("Polling for completion (max %ds)...", MAX_WAIT)
        deadline = time.time() + MAX_WAIT
        final_run: dict = run

        while time.time() < deadline:
            await asyncio.sleep(POLL_INTERVAL)
            poll = await client.get(f"/simulate/{run_id}")
            final_run = poll.json()
            elapsed = time.time() - start
            logger.info("  status=%-10s  elapsed=%.1fs", final_run["status"], elapsed)

            if final_run["status"] in ("complete", "failed"):
                break
        else:
            logger.error("Simulation did not complete within %ds", MAX_WAIT)
            sys.exit(1)

    elapsed = time.time() - start

    # 4. Results
    print("\n" + "=" * 60)
    print("DEMO SIMULATION COMPLETE")
    print("=" * 60)
    print(f"Run ID    : {run_id}")
    print(f"Status    : {final_run['status']}")
    print(f"Elapsed   : {elapsed:.1f}s  (limit: {MAX_WAIT}s)")
    print(f"Decision  : {DEMO_DECISION[:80]}...")
    if final_run.get("recommendation"):
        print(f"\nRecommendation:\n  {final_run['recommendation']}")
    print(f"\nReport URL: http://localhost:3000/report/{run_id}")
    print(f"API URL   : {API_BASE}/simulate/{run_id}")
    print("=" * 60)

    if elapsed >= MAX_WAIT:
        logger.error("FAILED: exceeded %ds target", MAX_WAIT)
        sys.exit(1)
    else:
        logger.info("SUCCESS: completed in %.1fs (under %ds target)", elapsed, MAX_WAIT)


def main() -> None:
    parser = argparse.ArgumentParser(description="OrgSim demo seed script")
    parser.add_argument("--skip-loaders", action="store_true", help="Skip data loader step")
    parser.add_argument("--start-api", action="store_true", help="Start uvicorn inline (background)")
    args = parser.parse_args()

    api_proc = None
    if args.start_api:
        logger.info("Starting API server on :8000...")
        backend_dir = Path(__file__).parents[1]
        api_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--port", "8000"],
            cwd=backend_dir,
        )

    try:
        logger.info("Waiting for API at %s...", API_BASE)
        if not _wait_for_api(timeout=30):
            logger.error("API not reachable at %s — start it first or use --start-api", API_BASE)
            sys.exit(1)

        if not args.skip_loaders:
            run_loaders()

        asyncio.run(run_demo())
    finally:
        if api_proc:
            api_proc.terminate()
            api_proc.wait()


if __name__ == "__main__":
    main()

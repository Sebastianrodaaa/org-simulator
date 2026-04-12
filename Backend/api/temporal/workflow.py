"""
OrgSim Temporal workflow.

Workflow: OrgSimWorkflow
  Activity 1: generate_personas   — reads seed reports, builds agent context
  Activity 2: run_simulation      — calls MiroFish simulation service
  Activity 3: extract_conflicts   — parses agent logs → structured conflicts
  Activity 4: generate_report     — compiles final decision report

Activities call HTTP endpoints on the simulation service (SIMULATION_SERVICE_URL).
All activities are idempotent and carry retry policies.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import httpx
from temporalio import activity, workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)

SIMULATION_SERVICE_URL = os.getenv("SIMULATION_SERVICE_URL", "http://localhost:8001")
TASK_QUEUE = "orgsim"

_RETRY = RetryPolicy(
    maximum_attempts=3,
    backoff_coefficient=2.0,
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(seconds=60),
    non_retryable_error_types=["ValueError"],
)


# ── Input / output models ─────────────────────────────────────────────────────

@dataclass
class WorkflowInput:
    run_id: str
    decision: str
    departments: list[str]


@dataclass
class PersonaSet:
    run_id: str
    personas: list[dict[str, Any]]


@dataclass
class SimulationResult:
    run_id: str
    agent_log: list[dict[str, Any]]
    raw_output: str


@dataclass
class ConflictSet:
    run_id: str
    conflicts: list[dict[str, Any]]


@dataclass
class FinalReport:
    run_id: str
    decision: str
    conflicts: list[dict[str, Any]]
    recommendation: str
    confidence: float
    summary: str


# ── Activities ────────────────────────────────────────────────────────────────

@activity.defn
async def generate_personas(inp: WorkflowInput) -> PersonaSet:
    """
    Call the simulation service to generate org-role personas from seed reports.
    Falls back to stub personas when the service is unreachable.
    """
    url = f"{SIMULATION_SERVICE_URL}/personas/generate"
    payload = {"run_id": inp.run_id, "decision": inp.decision, "departments": inp.departments}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            activity.logger.info("Personas generated for run %s: %d agents", inp.run_id, len(data["personas"]))
            return PersonaSet(run_id=inp.run_id, personas=data["personas"])
    except Exception as exc:
        activity.logger.warning("Simulation service unavailable, using stub personas: %s", exc)
        return PersonaSet(
            run_id=inp.run_id,
            personas=[
                {"name": "CFO", "role": "Chief Financial Officer", "dept": "Finance",
                 "bias": "cost_control", "budget_authority": 10},
                {"name": "VP Sales", "role": "VP of Sales", "dept": "Sales",
                 "bias": "pipeline_growth", "budget_authority": 7},
                {"name": "Ops Lead", "role": "Operations Lead", "dept": "Operations",
                 "bias": "capacity_protection", "budget_authority": 5},
                {"name": "HR Director", "role": "HR Director", "dept": "HR",
                 "bias": "retention_focus", "budget_authority": 4},
            ],
        )


@activity.defn
async def run_simulation(personas: PersonaSet) -> SimulationResult:
    """
    Call the MiroFish simulation service with the generated personas.
    Returns a structured agent interaction log.
    """
    url = f"{SIMULATION_SERVICE_URL}/simulation/run"
    payload = {"run_id": personas.run_id, "personas": personas.personas}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            activity.logger.info("Simulation complete for run %s: %d messages", personas.run_id, len(data["agent_log"]))
            return SimulationResult(
                run_id=personas.run_id,
                agent_log=data["agent_log"],
                raw_output=data.get("raw_output", ""),
            )
    except Exception as exc:
        activity.logger.warning("Simulation service unreachable, using stub result: %s", exc)
        return SimulationResult(
            run_id=personas.run_id,
            agent_log=[
                {"agent": "CFO", "message": "A 20% marketing budget cut saves $56k but risks Q4 pipeline coverage.", "type": "analysis"},
                {"agent": "VP Sales", "message": "Three enterprise deals close in Q4. Marketing support is critical.", "type": "objection"},
                {"agent": "Ops Lead", "message": "Engineering is at 94% capacity. We cannot absorb headcount reallocation.", "type": "constraint"},
                {"agent": "HR Director", "message": "Flight risk in Sales is elevated. Budget instability worsens retention.", "type": "risk"},
                {"agent": "CFO", "message": "Runway stays at 18 months regardless. This cut is discretionary.", "type": "analysis"},
                {"agent": "VP Sales", "message": "Estimated 12% velocity drop without campaign spend. $340k pipeline at risk.", "type": "conflict"},
                {"agent": "Ops Lead", "message": "Conflict: Sales depends on Engineering capacity (strength 9/10). Feature freeze looms.", "type": "conflict"},
                {"agent": "HR Director", "message": "Recommend 90-day hold rather than immediate cut. Review in Q1.", "type": "recommendation"},
            ],
            raw_output="stub",
        )


@activity.defn
async def extract_conflicts(result: SimulationResult) -> ConflictSet:
    """
    Call the conflict extractor service to parse agent logs into structured conflicts.
    Falls back to heuristic extraction from the log.
    """
    url = f"{SIMULATION_SERVICE_URL}/conflicts/extract"
    payload = {"run_id": result.run_id, "agent_log": result.agent_log}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return ConflictSet(run_id=result.run_id, conflicts=data["conflicts"])
    except Exception as exc:
        activity.logger.warning("Conflict extractor unavailable, using heuristic: %s", exc)
        conflicts = [
            entry for entry in result.agent_log if entry.get("type") == "conflict"
        ]
        return ConflictSet(
            run_id=result.run_id,
            conflicts=[
                {
                    "id": f"conflict-{i}",
                    "source_agent": c["agent"],
                    "message": c["message"],
                    "severity": "high",
                    "departments_affected": ["Sales", "Marketing"],
                }
                for i, c in enumerate(conflicts)
            ],
        )


@activity.defn
async def generate_report(result: SimulationResult, conflicts: ConflictSet) -> FinalReport:
    """
    Call the report generation service (DSPy-compiled) to produce a final decision report.
    Falls back to a templated stub report.
    """
    url = f"{SIMULATION_SERVICE_URL}/report/generate"
    payload = {
        "run_id": result.run_id,
        "agent_log": result.agent_log,
        "conflicts": conflicts.conflicts,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return FinalReport(
                run_id=result.run_id,
                decision=data["decision"],
                conflicts=conflicts.conflicts,
                recommendation=data["recommendation"],
                confidence=data["confidence"],
                summary=data["summary"],
            )
    except Exception as exc:
        activity.logger.warning("Report service unavailable, using stub report: %s", exc)
        return FinalReport(
            run_id=result.run_id,
            decision="CFO cuts Q4 marketing budget 20%",
            conflicts=conflicts.conflicts,
            recommendation="Defer immediate cut. Run a Q1 pilot at 10% reduction with 30-day review gate.",
            confidence=0.78,
            summary=(
                f"Simulation surfaced {len(conflicts.conflicts)} cross-department conflict(s). "
                "Sales pipeline risk is high given Q4 close dates. Engineering capacity constraint "
                "limits mitigation options. HR flags elevated flight risk. Recommended: defer to Q1."
            ),
        )


# ── Workflow ──────────────────────────────────────────────────────────────────

@workflow.defn
class OrgSimWorkflow:
    @workflow.run
    async def run(self, inp: WorkflowInput) -> FinalReport:
        workflow.logger.info("OrgSimWorkflow started: run_id=%s decision=%s", inp.run_id, inp.decision)

        personas = await workflow.execute_activity(
            generate_personas,
            inp,
            schedule_to_close_timeout=timedelta(minutes=5),
            retry_policy=_RETRY,
        )

        result = await workflow.execute_activity(
            run_simulation,
            personas,
            schedule_to_close_timeout=timedelta(minutes=10),
            retry_policy=_RETRY,
        )

        conflicts = await workflow.execute_activity(
            extract_conflicts,
            result,
            schedule_to_close_timeout=timedelta(minutes=2),
            retry_policy=_RETRY,
        )

        report = await workflow.execute_activity(
            generate_report,
            args=[result, conflicts],
            schedule_to_close_timeout=timedelta(minutes=3),
            retry_policy=_RETRY,
        )

        workflow.logger.info(
            "OrgSimWorkflow complete: run_id=%s conflicts=%d recommendation=%s",
            inp.run_id, len(report.conflicts), report.recommendation[:60],
        )
        return report

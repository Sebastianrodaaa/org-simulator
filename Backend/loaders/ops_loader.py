"""
Load infra/mock/ops_capacity.yaml into TypeDB.

Creates: Metric entities for Engineering and Operations departments.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from typedb.driver import TransactionType

if TYPE_CHECKING:
    from typedb.driver import Driver

from typedb_util import TYPEDB_DATABASE, execute_write_query

logger = logging.getLogger(__name__)

MOCK_DIR = Path(__file__).parents[2] / "infra" / "mock"


def _insert(tx, tql: str) -> None:
    execute_write_query(tx, tql)


def _insert_metric(
    driver: "Driver",
    metric_id: str,
    metric_name: str,
    value: str,
    unit: str,
    period: str,
    department_name: str,
) -> None:
    name_esc = metric_name.replace('"', '\\"')
    val_esc = value.replace("\\", "\\\\").replace('"', '\\"')
    dept_esc = department_name.replace('"', '\\"')
    with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
        _insert(
            tx,
            f'insert $m isa Metric, '
            f'has metric_id "{metric_id}", '
            f'has metric_name "{name_esc}", '
            f'has metric_value "{val_esc}", '
            f'has unit "{unit}", '
            f'has period "{period}", '
            f'has department_name "{dept_esc}";',
        )
        tx.commit()


def load_ops(driver: "Driver") -> None:
    yaml_path = MOCK_DIR / "ops_capacity.yaml"
    logger.info("Loading ops capacity from %s", yaml_path)

    data: dict = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    metric_count = 0

    # Insert Engineering and Operations department entities
    for dept_name, budget, headcount, desc in [
        ("Engineering", 2400000.0, 34, "Product engineering and infrastructure"),
        ("Operations", 760000.0, 10, "DevOps and operational excellence"),
    ]:
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            _insert(
                tx,
                f'insert $dept isa Department, '
                f'has name "{dept_name}", '
                f'has description "{desc}", '
                f'has budget_usd {budget}, '
                f'has headcount {headcount};',
            )
            tx.commit()

    eng = data["engineering"]

    scalar_metrics: list[tuple[str, str, str]] = [
        ("capacity_pct", str(eng["capacity_pct"]), "percent"),
        ("open_incidents_p1", str(eng["open_incidents_p1"]), "count"),
        ("open_incidents_p2", str(eng["open_incidents_p2"]), "count"),
        ("infra_monthly_cost_usd", str(eng["infra_monthly_cost_usd"]), "usd"),
        ("sprint_velocity", str(eng["sprint_velocity"]), "points"),
        ("open_reqs", str(eng["open_reqs"]), "count"),
        ("total_headcount", str(eng["total_headcount"]), "count"),
    ]
    for name, val, unit in scalar_metrics:
        _insert_metric(
            driver,
            metric_id=f"METRIC-ENG-{name.upper()}-Q4-2025",
            metric_name=name,
            value=val,
            unit=unit,
            period="Q4_2025",
            department_name="Engineering",
        )
        metric_count += 1

    # planned_features_q4 stored as JSON string
    features_json = json.dumps(eng["planned_features_q4"])
    _insert_metric(
        driver,
        metric_id="METRIC-ENG-PLANNED-FEATURES-Q4-2025",
        metric_name="planned_features_q4",
        value=features_json,
        unit="json",
        period="Q4_2025",
        department_name="Engineering",
    )
    metric_count += 1

    # DevOps / Operations metrics
    devops = data["devops"]
    devops_metrics: list[tuple[str, str, str]] = [
        ("total_headcount", str(devops["total_headcount"]), "count"),
        ("capacity_pct", str(devops["capacity_pct"]), "percent"),
        ("uptime_30d_pct", str(devops["uptime_30d_pct"]), "percent"),
        ("deploy_frequency_per_week", str(devops["deploy_frequency_per_week"]), "count"),
    ]
    for name, val, unit in devops_metrics:
        _insert_metric(
            driver,
            metric_id=f"METRIC-DEVOPS-{name.upper()}-Q4-2025",
            metric_name=name,
            value=val,
            unit=unit,
            period="Q4_2025",
            department_name="Operations",
        )
        metric_count += 1

    logger.info("Ops loader complete — metrics: %d", metric_count)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from typedb_util import open_typedb_driver

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    with open_typedb_driver() as driver:
        load_ops(driver)

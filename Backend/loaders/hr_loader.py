"""
Load infra/mock/hr_people.json into TypeDB.

Creates: Metric entities for each department and company-wide metrics.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

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
    dept_esc = department_name.replace('"', '\\"')
    with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
        _insert(
            tx,
            f'insert $m isa Metric, '
            f'has metric_id "{metric_id}", '
            f'has metric_name "{metric_name}", '
            f'has metric_value "{value}", '
            f'has unit "{unit}", '
            f'has period "{period}", '
            f'has department_name "{dept_esc}";',
        )
        tx.commit()


def load_hr(driver: "Driver") -> None:
    json_path = MOCK_DIR / "hr_people.json"
    logger.info("Loading HR people data from %s", json_path)

    data: dict = json.loads(json_path.read_text(encoding="utf-8"))
    metric_count = 0

    # Insert HR department entity
    with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
        _insert(
            tx,
            'insert $dept isa Department, '
            'has name "HR", '
            'has description "Human resources and people operations", '
            'has budget_usd 480000.0, '
            'has headcount 7;',
        )
        tx.commit()

    # Per-department HR metrics
    field_meta: dict[str, tuple[str, str]] = {
        "headcount": ("count", "headcount"),
        "attrition_rate_annual_pct": ("percent", "attrition_rate_annual_pct"),
        "open_reqs": ("count", "open_reqs"),
        "avg_tenure_months": ("months", "avg_tenure_months"),
        "engagement_score": ("score_1_10", "engagement_score"),
        "top_performer_flight_risk": ("count", "top_performer_flight_risk"),
    }

    for dept_name, dept_data in data["departments"].items():
        dept_key = dept_name.upper().replace(" ", "_")
        for field, (unit, metric_name) in field_meta.items():
            val = dept_data.get(field)
            if val is None:
                continue
            _insert_metric(
                driver,
                metric_id=f"METRIC-HR-{dept_key}-{field.upper()}-2025",
                metric_name=metric_name,
                value=str(val),
                unit=unit,
                period="FY_2025",
                department_name=dept_name,
            )
            metric_count += 1

    # Company-wide metrics (stored under "Company" department)
    for name, val, unit in [
        ("engagement_score", str(data["company_wide"]["engagement_score"]), "score_1_10"),
        ("attrition_rate_annual_pct", str(data["company_wide"]["attrition_rate_annual_pct"]), "percent"),
        ("nps_internal", str(data["company_wide"]["nps_internal"]), "nps"),
    ]:
        _insert_metric(
            driver,
            metric_id=f"METRIC-COMPANY-{name.upper()}-2025",
            metric_name=name,
            value=val,
            unit=unit,
            period="FY_2025",
            department_name="Company",
        )
        metric_count += 1

    logger.info("HR loader complete — metrics: %d", metric_count)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from typedb_util import open_typedb_driver

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    with open_typedb_driver() as driver:
        load_hr(driver)

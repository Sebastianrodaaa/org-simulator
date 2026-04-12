"""
Load infra/mock/finance_pl.json into TypeDB.

Creates: BudgetLine entities, Metric entities for cost centers and runway.
Also creates the Marketing department entity (budget is owned by Finance).
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


def load_finance(driver: "Driver") -> None:
    json_path = MOCK_DIR / "finance_pl.json"
    logger.info("Loading finance P&L from %s", json_path)

    data: dict = json.loads(json_path.read_text(encoding="utf-8"))
    budget_count = metric_count = 0

    # Insert Finance and Marketing department entities
    for dept_name, budget, headcount, desc in [
        ("Finance", 480000.0, 8, "Financial planning and analysis"),
        ("Marketing", 980000.0, 12, "Demand generation and brand marketing"),
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

    # Budget lines
    for bl in data["budget_lines"]:
        dept = bl["dept"].replace('"', '\\"')
        budget_id = f"BL-{bl['dept'].upper().replace(' ', '-')}-2025"
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            _insert(
                tx,
                f'insert $b isa BudgetLine, '
                f'has budget_id "{budget_id}", '
                f'has dept_name "{dept}", '
                f'has allocated_usd {float(bl["allocated_usd"])}, '
                f'has spent_usd {float(bl["spent_usd"])}, '
                f'has remaining_usd {float(bl["remaining_usd"])};',
            )
            tx.commit()
        budget_count += 1

    # Runway metric
    with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
        _insert(
            tx,
            f'insert $m isa Metric, '
            f'has metric_id "METRIC-FINANCE-RUNWAY-2025", '
            f'has metric_name "runway_months", '
            f'has metric_value "{data["runway_months"]}", '
            f'has unit "months", '
            f'has period "FY_2025", '
            f'has department_name "Finance";',
        )
        tx.commit()
    metric_count += 1

    # Q4 forecast metrics
    for key, val in data["quarters"]["Q4_forecast"].items():
        metric_id = f"METRIC-FINANCE-Q4-{key.upper()}"
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            _insert(
                tx,
                f'insert $m isa Metric, '
                f'has metric_id "{metric_id}", '
                f'has metric_name "{key}", '
                f'has metric_value "{val}", '
                f'has unit "usd", '
                f'has period "Q4_2025", '
                f'has department_name "Finance";',
            )
            tx.commit()
        metric_count += 1

    # Cost center metrics
    for dept_name, costs in data["cost_centers"].items():
        dept_key = dept_name.upper().replace(" ", "_")
        for cost_key, cost_val in costs.items():
            metric_id = f"METRIC-{dept_key}-{cost_key.upper()}-2025"
            with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                _insert(
                    tx,
                    f'insert $m isa Metric, '
                    f'has metric_id "{metric_id}", '
                    f'has metric_name "{cost_key}", '
                    f'has metric_value "{cost_val}", '
                    f'has unit "usd", '
                    f'has period "FY_2025", '
                    f'has department_name "{dept_name}";',
                )
                tx.commit()
            metric_count += 1

    logger.info(
        "Finance loader complete — budget_lines: %d, metrics: %d",
        budget_count, metric_count,
    )


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from typedb_util import open_typedb_driver

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    with open_typedb_driver() as driver:
        load_finance(driver)

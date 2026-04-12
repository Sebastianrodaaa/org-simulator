"""
Load infra/mock/sales_pipeline.csv into TypeDB.

Creates: Deal, Employee, Product entities and Ownership relations.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from typedb.driver import TransactionType

if TYPE_CHECKING:
    from typedb.driver import Driver

from typedb_util import TYPEDB_DATABASE, execute_write_query

logger = logging.getLogger(__name__)

MOCK_DIR = Path(__file__).parents[2] / "infra" / "mock"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _insert(tx, tql: str) -> None:
    """Execute an insert query, consuming the iterator so the write executes."""
    execute_write_query(tx, tql)


def load_sales(driver: "Driver") -> None:
    csv_path = MOCK_DIR / "sales_pipeline.csv"
    logger.info("Loading sales pipeline from %s", csv_path)

    rows: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    employees_seen: set[str] = set()
    products_seen: set[str] = set()
    deal_count = emp_count = prod_count = rel_count = 0

    # Pass 1: insert Sales department
    with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
        _insert(
            tx,
            'insert $dept isa Department, has name "Sales", '
            'has description "Revenue-generating sales organization", '
            'has budget_usd 1200000.0, '
            'has headcount 18;',
        )
        tx.commit()

    # Pass 2: insert unique employees
    for row in rows:
        owner_name = _escape(row["owner"].strip())
        department = _escape(row["department"].strip())
        employee_id = f"EMP-{row['owner'].strip().replace(' ', '-').upper()}"
        if employee_id not in employees_seen:
            with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                _insert(
                    tx,
                    f'insert $e isa Employee, '
                    f'has employee_id "{employee_id}", '
                    f'has name "{owner_name}", '
                    f'has department_name "{department}", '
                    f'has title "Account Executive", '
                    f'has seniority "mid";',
                )
                tx.commit()
            employees_seen.add(employee_id)
            emp_count += 1

    # Pass 3: insert unique products
    for row in rows:
        product_name = _escape(row["product"].strip())
        product_id = f"PROD-{row['product'].strip().replace(' ', '-').upper()}"
        if product_id not in products_seen:
            with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
                _insert(
                    tx,
                    f'insert $p isa Product, '
                    f'has product_id "{product_id}", '
                    f'has name "{product_name}", '
                    f'has category "SaaS";',
                )
                tx.commit()
            products_seen.add(product_id)
            prod_count += 1

    # Pass 4: insert deals + ownership relations
    for row in rows:
        deal_id = row["deal_id"].strip()
        deal_name = _escape(row["deal_name"].strip())
        value_usd = float(row["value_usd"].strip())
        stage = _escape(row["stage"].strip())
        close_date = row["close_date"].strip()
        probability_pct = int(row["probability_pct"].strip())
        employee_id = f"EMP-{row['owner'].strip().replace(' ', '-').upper()}"

        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            _insert(
                tx,
                f'insert $d isa Deal, '
                f'has deal_id "{deal_id}", '
                f'has deal_name "{deal_name}", '
                f'has value_usd {value_usd}, '
                f'has stage "{stage}", '
                f'has probability_pct {probability_pct}, '
                f'has close_date "{close_date}";',
            )
            tx.commit()
        deal_count += 1

        # Ownership in a separate transaction (employee already committed)
        with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
            _insert(
                tx,
                f'match '
                f'  $e isa Employee, has employee_id "{employee_id}"; '
                f'  $d isa Deal, has deal_id "{deal_id}"; '
                f'insert (owner: $e, asset: $d) isa Ownership;',
            )
            tx.commit()
        rel_count += 1

    logger.info(
        "Sales loader complete — deals: %d, employees: %d, products: %d, ownership relations: %d",
        deal_count, emp_count, prod_count, rel_count,
    )


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from typedb_util import open_typedb_driver

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    with open_typedb_driver() as driver:
        load_sales(driver)

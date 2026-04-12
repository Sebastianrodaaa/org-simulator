"""
Integration tests for Phase 1: TypeDB schema and loaded data.

Prerequisites:
  - TypeDB running at TYPEDB_HOST:TYPEDB_PORT
  - All loaders (run_all.py) and seed reports already executed

Run:
  pytest Backend/tests/test_schema.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from typedb_util import TYPEDB_DATABASE, fetch_rows_read, open_typedb_driver

OUTPUT_DIR = Path(__file__).parents[1] / "output"


@pytest.fixture(scope="session")
def driver():
    with open_typedb_driver() as drv:
        yield drv


@pytest.fixture(scope="session")
def data_session(driver):
    """Legacy name: yields the driver (typedb-driver 3.x has no sessions)."""
    yield driver


def _fetch_all(driver, query: str) -> list[dict]:
    """Run a select query and return all rows as {var: value} dicts."""
    rows = fetch_rows_read(driver, TYPEDB_DATABASE, query)
    return [dict(r) for r in rows]


def _fetch_first(driver, query: str) -> dict | None:
    rows = _fetch_all(driver, query)
    return rows[0] if rows else None


class TestDepartments:
    def test_at_least_four_departments_exist(self, data_session):
        rows = _fetch_all(data_session, "match $d isa Department, has name $n; select $n;")
        assert len(rows) >= 4, f"Expected ≥4 departments, got {len(rows)}"

    def test_sales_department_exists(self, data_session):
        row = _fetch_first(
            data_session,
            'match $d isa Department, has name "Sales"; select $d;',
        )
        assert row is not None, "Sales department not found"

    def test_engineering_department_exists(self, data_session):
        row = _fetch_first(
            data_session,
            'match $d isa Department, has name "Engineering"; select $d;',
        )
        assert row is not None, "Engineering department not found"


class TestCrossDeptDependencies:
    def test_at_least_three_dependencies_exist(self, data_session):
        rows = _fetch_all(
            data_session,
            "match $r isa CrossDeptDependency, has dependency_type $dt; select $dt;",
        )
        assert len(rows) >= 3, f"Expected ≥3 CrossDeptDependency relations, got {len(rows)}"

    def test_sales_depends_on_engineering(self, data_session):
        row = _fetch_first(
            data_session,
            'match '
            '$x isa CrossDeptDependency (dependent_dept: $s, dependency_dept: $e), '
            'has dependency_type $dt; '
            '$s isa Department, has name "Sales"; '
            '$e isa Department, has name "Engineering"; '
            'select $dt;',
        )
        assert row is not None, "Sales→Engineering CrossDeptDependency not found"
        assert row.get("dt") == "capacity"

    def test_sales_depends_on_marketing(self, data_session):
        row = _fetch_first(
            data_session,
            'match '
            '$x isa CrossDeptDependency (dependent_dept: $s, dependency_dept: $m), '
            'has dependency_type $dt; '
            '$s isa Department, has name "Sales"; '
            '$m isa Department, has name "Marketing"; '
            'select $dt;',
        )
        assert row is not None, "Sales→Marketing CrossDeptDependency not found"
        assert row.get("dt") == "budget"


class TestBudgetLines:
    def test_marketing_budget_line_exists_with_remaining(self, data_session):
        row = _fetch_first(
            data_session,
            'match $b isa BudgetLine, has dept_name "Marketing", has remaining_usd $r; '
            'select $r;',
        )
        assert row is not None, "Marketing BudgetLine not found"
        assert float(row["r"]) > 0, f"Marketing remaining_usd should be >0, got {row['r']}"

    def test_all_four_budget_lines_exist(self, data_session):
        rows = _fetch_all(data_session, "match $b isa BudgetLine, has budget_id $id; select $id;")
        assert len(rows) >= 4, f"Expected ≥4 budget lines, got {len(rows)}"


class TestMetrics:
    def test_engineering_capacity_pct_above_85(self, data_session):
        row = _fetch_first(
            data_session,
            'match $m isa Metric, '
            'has metric_name "capacity_pct", '
            'has metric_value $v, '
            'has department_name "Engineering"; '
            'select $v;',
        )
        assert row is not None, "Engineering capacity_pct metric not found"
        assert float(row["v"]) > 85, f"Engineering capacity_pct expected >85, got {row['v']}"

    def test_hr_attrition_metrics_exist(self, data_session):
        rows = _fetch_all(
            data_session,
            'match $m isa Metric, has metric_name "attrition_rate_annual_pct", '
            'has department_name $dn; select $dn;',
        )
        assert len(rows) >= 4, f"Expected ≥4 attrition metrics (one per dept), got {len(rows)}"


class TestSeedReports:
    def test_four_seed_report_files_exist(self):
        for filename in ["sales_seed.md", "finance_seed.md", "engineering_seed.md", "hr_seed.md"]:
            path = OUTPUT_DIR / filename
            assert path.exists(), f"Seed report not found: {path}"
            assert path.stat().st_size > 0, f"Seed report is empty: {path}"

    def test_sales_seed_contains_deals_section(self):
        path = OUTPUT_DIR / "sales_seed.md"
        if not path.exists():
            pytest.skip("sales_seed.md not yet generated")
        assert "Deals in pipeline" in path.read_text(encoding="utf-8")

    def test_engineering_seed_contains_metrics(self):
        path = OUTPUT_DIR / "engineering_seed.md"
        if not path.exists():
            pytest.skip("engineering_seed.md not yet generated")
        assert "## Key Metrics" in path.read_text(encoding="utf-8")

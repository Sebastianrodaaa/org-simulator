"""
Seed report generator — queries TypeDB per department and writes structured
markdown reports consumed by the MiroFish simulation agent.

Output: backend/output/{dept_lowercase}_seed.md
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typedb.driver import Driver

from typedb_util import TYPEDB_DATABASE, fetch_rows_read, open_typedb_driver

logger = logging.getLogger(__name__)
OUTPUT_DIR = Path(__file__).parents[1] / "output"

DEPARTMENTS = ["Sales", "Finance", "Engineering", "HR", "Operations"]

RISK_THRESHOLDS: dict[str, tuple[float, str]] = {
    "capacity_pct": (90.0, "Capacity >90% — risk of overcommitment"),
    "attrition_rate_annual_pct": (15.0, "Attrition >15% — retention risk"),
    "open_incidents_p1": (3.0, "P1 incidents >3 — operational instability"),
    "top_performer_flight_risk": (2.0, "Top performer flight risk ≥2 — talent loss exposure"),
}


def _run_query(driver: "Driver", query: str) -> list[dict]:
    """Execute a read query and return results as list of variable->value dicts."""
    rows = fetch_rows_read(driver, TYPEDB_DATABASE, query)
    return [dict(r) for r in rows]


def generate_report(driver: "Driver", dept_name: str) -> str:
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    metrics = _run_query(
        driver,
        f'match $m isa Metric, '
        f'has metric_name $mn, has metric_value $v, has period $p, '
        f'has department_name "{dept_name}"; '
        f'select $mn, $v, $p;',
    )

    budget_lines = _run_query(
        driver,
        f'match $b isa BudgetLine, has dept_name "{dept_name}", '
        f'has allocated_usd $a, has spent_usd $s, has remaining_usd $r; '
        f'select $a, $s, $r;',
    )

    deps_outgoing = _run_query(
        driver,
        f'match '
        f'$xdep isa CrossDeptDependency '
        f'(dependent_dept: $dep_dept, dependency_dept: $dep_on), '
        f'has dependency_type $dt, has strength $st; '
        f'$dep_dept isa Department, has name "{dept_name}"; '
        f'$dep_on isa Department, has name $dn; '
        f'select $dn, $dt, $st;',
    )

    deps_incoming = _run_query(
        driver,
        f'match '
        f'$xdep isa CrossDeptDependency '
        f'(dependent_dept: $dep_dept, dependency_dept: $dep_on), '
        f'has dependency_type $dt, has strength $st; '
        f'$dep_dept isa Department, has name $dn; '
        f'$dep_on isa Department, has name "{dept_name}"; '
        f'select $dn, $dt, $st;',
    )

    deals: list[dict] = []
    deal_total = 0.0
    if dept_name == "Sales":
        deals = _run_query(
            driver,
            'match $d isa Deal, has deal_id $did, has value_usd $v, has stage $s; '
            'select $did, $v, $s;',
        )
        deal_total = sum(float(d.get("v", 0)) for d in deals)

    open_reqs_rows = _run_query(
        driver,
        f'match $m isa Metric, has metric_name "open_reqs", '
        f'has metric_value $v, has department_name "{dept_name}"; '
        f'select $v;',
    )
    open_reqs = int(float(open_reqs_rows[0]["v"])) if open_reqs_rows else 0

    lines: list[str] = []
    lines.append(f"# {dept_name} Department Simulation Report")
    lines.append(f"Generated: {now}")
    lines.append("")

    lines.append("## Key Metrics")
    lines.append("| Metric | Value | Period |")
    lines.append("|--------|-------|--------|")
    for m in metrics:
        mn = m.get("mn", "")
        if mn == "planned_features_q4":
            continue
        lines.append(f"| {mn} | {m.get('v', '')} | {m.get('p', '')} |")
    lines.append("")

    lines.append("## Budget Status")
    if budget_lines:
        lines.append("| Line | Allocated (USD) | Spent (USD) | Remaining (USD) |")
        lines.append("|------|----------------|-------------|-----------------|")
        for bl in budget_lines:
            a = f"${float(bl.get('a', 0)):,.0f}"
            s = f"${float(bl.get('s', 0)):,.0f}"
            r = f"${float(bl.get('r', 0)):,.0f}"
            lines.append(f"| {dept_name} | {a} | {s} | {r} |")
    else:
        lines.append("_No direct budget line for this department._")
    lines.append("")

    lines.append("## Dependencies")
    for d in deps_outgoing:
        lines.append(f"- Depends on **{d.get('dn')}** for {d.get('dt')} (strength: {d.get('st')}/10)")
    for d in deps_incoming:
        lines.append(f"- **{d.get('dn')}** depends on us for {d.get('dt')} (strength: {d.get('st')}/10)")
    if not deps_outgoing and not deps_incoming:
        lines.append("_No cross-department dependencies recorded._")
    lines.append("")

    lines.append("## Risk Indicators")
    metric_lookup: dict[str, float] = {}
    for m in metrics:
        try:
            metric_lookup[m.get("mn", "")] = float(m.get("v", 0))
        except (ValueError, TypeError):
            pass
    risks = [
        f"- **{label}** (current: {metric_lookup[mn]})"
        for mn, (threshold, label) in RISK_THRESHOLDS.items()
        if mn in metric_lookup and metric_lookup[mn] >= threshold
    ]
    lines.extend(risks if risks else ["_No risk thresholds exceeded._"])
    lines.append("")

    lines.append("## Entities")
    if dept_name == "Sales" and deals:
        lines.append(f"- Deals in pipeline: **{len(deals)}** (${deal_total:,.0f} total value)")
    if open_reqs > 0:
        lines.append(f"- Open requisitions: **{open_reqs}**")
    for m in metrics:
        if m.get("mn") == "planned_features_q4":
            try:
                features = json.loads(m["v"])
                lines.append(f"- Planned Q4 features: **{len(features)}**")
                for feat in features:
                    lines.append(f"  - {feat}")
            except Exception:
                pass
    lines.append("")

    return "\n".join(lines)


def generate_all_reports(driver: "Driver") -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for dept in DEPARTMENTS:
        logger.info("Generating seed report for %s", dept)
        try:
            content = generate_report(driver, dept)
            out_path = OUTPUT_DIR / f"{dept.lower()}_seed.md"
            out_path.write_text(content, encoding="utf-8")
            logger.info("Wrote %s", out_path)
        except Exception as exc:
            logger.error("Failed to generate report for %s: %s", dept, exc, exc_info=True)
            errors.append(f"{dept}: {exc}")
    if errors:
        raise RuntimeError("seed_reports: " + "; ".join(errors))


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    with open_typedb_driver() as driver:
        generate_all_reports(driver)

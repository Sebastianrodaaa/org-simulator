"""
OrgSim Cascade Tracer
=====================
Queries the TypeDB CrossDeptDependency relations to build a cascade impact
map for a given decision and set of primary departments.

The traversal covers:
    - Direct (1-hop) dependencies: depts directly linked to primary_depts
    - Indirect (2-hop) dependencies: depts linked through an intermediate dept

Impact severity is estimated from the ``strength_score`` attribute stored on
each CrossDeptDependency relation.

CascadeMap shape
----------------
{
    "decision": str,
    "primary_impact": [
        {"dept": str, "severity": str, "reason": str},
        ...
    ],
    "secondary_impact": [
        {"dept": str, "severity": str, "via": str, "reason": str},
        ...
    ],
}

Severity bands (strength_score → severity string):
    ≥ 0.7  → "high"
    ≥ 0.4  → "medium"
    else   → "low"
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TypeDB helpers
# ---------------------------------------------------------------------------

_TYPEDB_URI = os.getenv("TYPEDB_URI", "localhost:1729")
_TYPEDB_DB = os.getenv("TYPEDB_DATABASE", "orgsim")
_TYPEDB_USER = os.getenv("TYPEDB_USER", "admin")
_TYPEDB_PASSWORD = os.getenv("TYPEDB_PASSWORD", "password")

CascadeMap = dict[str, Any]


def _severity_from_score(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _connect_typedb() -> Any:
    """Return a TypeDB 3.x Core driver (caller must ``close()`` or use as context manager)."""
    from typedb.driver import Credentials, DriverOptions, TypeDB  # type: ignore

    creds = Credentials(_TYPEDB_USER, _TYPEDB_PASSWORD)
    opts = DriverOptions(is_tls_enabled=False)
    connect = getattr(TypeDB, "driver", None) or getattr(TypeDB, "core_driver", None)
    if connect is None:
        raise RuntimeError("typedb-driver missing TypeDB.driver / TypeDB.core_driver")
    return connect(_TYPEDB_URI, creds, opts)


# ---------------------------------------------------------------------------
# TypeQL queries
# ---------------------------------------------------------------------------

_DIRECT_DEPS_QUERY = """
match
  $source isa Department, has name "{dept_name}";
  $target isa Department, has name $target_name;
  $dep isa CrossDeptDependency (dependent_dept: $source, dependency_dept: $target),
       has strength $score,
       has dependency_type $dep_type;
select $target_name, $score, $dep_type;
"""

_INDIRECT_DEPS_QUERY = """
match
  $a isa Department, has name "{dept_name}";
  $b isa Department, has name $b_name;
  $c isa Department, has name $c_name;
  $dep1 isa CrossDeptDependency (dependent_dept: $a, dependency_dept: $b), has strength $score1;
  $dep2 isa CrossDeptDependency (dependent_dept: $b, dependency_dept: $c), has strength $score2;
  not {{ $c isa Department, has name "{dept_name}"; }};
select $b_name, $c_name, $score1, $score2;
"""


# ---------------------------------------------------------------------------
# Fallback: rule-based cascade when TypeDB is unavailable
# ---------------------------------------------------------------------------

# Known cross-dept relationships (mirrors entity_resolver.py seeds)
_STATIC_DEPS: dict[str, list[tuple[str, float, str]]] = {
    "Finance":     [("Sales", 0.8, "budget controls sales investment"),
                    ("HR", 0.6, "headcount budget approved by Finance"),
                    ("Operations", 0.5, "infra budget approved by Finance")],
    "Sales":       [("Operations", 0.7, "sales commitments drive ops capacity"),
                    ("Finance", 0.8, "revenue targets fund Finance runway")],
    "Operations":  [("Sales", 0.7, "ops capacity gates sales delivery"),
                    ("Finance", 0.5, "infra cost reported to Finance")],
    "HR":          [("Finance", 0.6, "hiring plan constrained by Finance budget"),
                    ("Sales", 0.5, "talent availability affects Sales headcount"),
                    ("Operations", 0.5, "retention risk affects ops staffing")],
}


def _fallback_cascade(decision: str, primary_depts: list[str]) -> CascadeMap:
    """
    Rule-based cascade map using static dependency table.
    Used when TypeDB is not running.
    """
    primary_impact: list[dict[str, Any]] = []
    secondary_impact: list[dict[str, Any]] = []
    seen_primary: set[str] = set(primary_depts)
    seen_secondary: set[str] = set()

    for dept in primary_depts:
        for (target, score, reason) in _STATIC_DEPS.get(dept, []):
            if target in seen_primary:
                continue
            severity = _severity_from_score(score)
            primary_impact.append({"dept": target, "severity": severity, "reason": reason})
            seen_primary.add(target)

            # Second hop from the direct target
            for (target2, score2, reason2) in _STATIC_DEPS.get(target, []):
                if target2 in seen_primary or target2 in seen_secondary:
                    continue
                combined_score = score * score2
                secondary_impact.append({
                    "dept": target2,
                    "severity": _severity_from_score(combined_score),
                    "via": target,
                    "reason": reason2,
                })
                seen_secondary.add(target2)

    return {
        "decision": decision,
        "primary_impact": primary_impact,
        "secondary_impact": secondary_impact,
    }


# ---------------------------------------------------------------------------
# TypeDB-backed traversal
# ---------------------------------------------------------------------------


def _query_direct(driver: Any, dept_name: str) -> list[tuple[str, float, str]]:
    """Return list of (target_dept, strength, dep_type) for one source dept."""
    from typedb.driver import TransactionType  # type: ignore

    results: list[tuple[str, float, str]] = []
    query = _DIRECT_DEPS_QUERY.format(dept_name=dept_name)
    with driver.transaction(_TYPEDB_DB, TransactionType.READ) as tx:
        qa = tx.query(query).resolve()
        if not qa.is_concept_rows():
            return results
        for row in qa.as_concept_rows():
            target_name = row.get("target_name").as_attribute().get_value()
            score = float(row.get("score").as_attribute().get_value())
            dep_type = row.get("dep_type").as_attribute().get_value()
            results.append((str(target_name), score, str(dep_type)))
    return results


def _query_indirect(driver: Any, dept_name: str) -> list[tuple[str, str, float, float]]:
    """Return list of (via_dept, target_dept, score1, score2)."""
    from typedb.driver import TransactionType  # type: ignore

    results: list[tuple[str, str, float, float]] = []
    query = _INDIRECT_DEPS_QUERY.format(dept_name=dept_name)
    with driver.transaction(_TYPEDB_DB, TransactionType.READ) as tx:
        qa = tx.query(query).resolve()
        if not qa.is_concept_rows():
            return results
        for row in qa.as_concept_rows():
            via = str(row.get("b_name").as_attribute().get_value())
            target = str(row.get("c_name").as_attribute().get_value())
            s1 = float(row.get("score1").as_attribute().get_value())
            s2 = float(row.get("score2").as_attribute().get_value())
            results.append((via, target, s1, s2))
    return results


def _typedb_cascade(decision: str, primary_depts: list[str]) -> CascadeMap:
    """Full TypeDB-backed cascade traversal."""
    with _connect_typedb() as driver:
        primary_impact: list[dict[str, Any]] = []
        secondary_impact: list[dict[str, Any]] = []
        seen: set[str] = set(primary_depts)

        for dept in primary_depts:
            # Direct (1-hop)
            for (target, score, dep_type) in _query_direct(driver, dept):
                if target in seen:
                    continue
                seen.add(target)
                primary_impact.append({
                    "dept": target,
                    "severity": _severity_from_score(score),
                    "reason": f"{dept} → {target}: {dep_type} (strength={score:.2f})",
                })

            # Indirect (2-hop)
            for (via, target, s1, s2) in _query_indirect(driver, dept):
                if target in seen:
                    continue
                seen.add(target)
                combined = s1 * s2
                secondary_impact.append({
                    "dept": target,
                    "severity": _severity_from_score(combined),
                    "via": via,
                    "reason": (
                        f"{dept} → {via} (strength={s1:.2f}) → {target} (strength={s2:.2f})"
                    ),
                })

        return {
            "decision": decision,
            "primary_impact": primary_impact,
            "secondary_impact": secondary_impact,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def trace_cascade(decision: str, primary_depts: list[str]) -> CascadeMap:
    """
    Produce a cascade impact map for the given decision and primary departments.

    Attempts a live TypeDB query first; falls back to the static dependency
    table when TypeDB is not reachable.

    Parameters
    ----------
    decision : str
        The proposed business decision (used as the map label).
    primary_depts : list[str]
        Departments that are directly and immediately affected by the decision.

    Returns
    -------
    CascadeMap dict with keys: decision, primary_impact, secondary_impact.
    """
    if not primary_depts:
        return {"decision": decision, "primary_impact": [], "secondary_impact": []}

    try:
        result = _typedb_cascade(decision, primary_depts)
        # If TypeDB is running but the DB hasn't been populated yet (loaders not run),
        # all queries return 0 rows — detect this and use the static fallback instead.
        if not result["primary_impact"] and any(d in _STATIC_DEPS for d in primary_depts):
            logger.warning(
                "TypeDB returned 0 impacts for known departments %s — DB likely unpopulated, "
                "using static fallback",
                primary_depts,
            )
            raise RuntimeError("TypeDB DB appears unpopulated")
        logger.info(
            "Cascade (TypeDB): %d primary, %d secondary impacts",
            len(result["primary_impact"]),
            len(result["secondary_impact"]),
        )
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "TypeDB cascade query failed (%s) — using static fallback", exc
        )
        result = _fallback_cascade(decision, primary_depts)
        logger.info(
            "Cascade (fallback): %d primary, %d secondary impacts",
            len(result["primary_impact"]),
            len(result["secondary_impact"]),
        )
        return result

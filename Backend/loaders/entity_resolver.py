"""
Entity resolver — creates CrossDeptDependency relations between departments
after all individual loaders have run.

Dependencies modelled:
  Sales      →depends_on→ Marketing    (type=budget,    strength=8)
  Sales      →depends_on→ Engineering  (type=capacity,  strength=9)
  Operations →depends_on→ HR           (type=headcount, strength=7)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from typedb.driver import TransactionType

if TYPE_CHECKING:
    from typedb.driver import Driver

from typedb_util import TYPEDB_DATABASE, execute_write_query

logger = logging.getLogger(__name__)


def _create_cross_dep(
    driver: "Driver",
    dependent: str,
    dependency: str,
    dep_type: str,
    strength: int,
) -> None:
    with driver.transaction(TYPEDB_DATABASE, TransactionType.WRITE) as tx:
        execute_write_query(
            tx,
            f'match '
            f'  $dep_dept isa Department, has name "{dependent}"; '
            f'  $dep_on isa Department, has name "{dependency}"; '
            f'insert '
            f'  (dependent_dept: $dep_dept, dependency_dept: $dep_on) isa CrossDeptDependency, '
            f'  has dependency_type "{dep_type}", '
            f'  has strength {strength};',
        )
        tx.commit()
    logger.info(
        "CrossDeptDependency: %s →[%s, strength=%d]→ %s",
        dependent, dep_type, strength, dependency,
    )


def resolve_entities(driver: "Driver") -> None:
    logger.info("Running entity resolver — creating cross-dept dependencies")

    dependencies: list[tuple[str, str, str, int]] = [
        ("Sales", "Marketing", "budget", 8),
        ("Sales", "Engineering", "capacity", 9),
        ("Operations", "HR", "headcount", 7),
    ]

    for dependent, dependency, dep_type, strength in dependencies:
        _create_cross_dep(driver, dependent, dependency, dep_type, strength)

    logger.info("Entity resolver complete — CrossDeptDependency relations created: %d", len(dependencies))


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from typedb_util import open_typedb_driver

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    with open_typedb_driver() as driver:
        resolve_entities(driver)

"""
Run all loaders in the correct order.

  1. init_db     — create database, load schema
  2. sales       — CSV → TypeDB
  3. finance     — JSON → TypeDB (also creates Marketing dept)
  4. ops         — YAML → TypeDB
  5. hr          — JSON → TypeDB
  6. resolver    — cross-dept dependency relations
  7. reports     — generate seed markdown reports

Each step is isolated; a single failure does not abort the rest.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from typedb_util import open_typedb_driver

from schema.init_db import init_database
from loaders.sales_loader import load_sales
from loaders.finance_loader import load_finance
from loaders.ops_loader import load_ops
from loaders.hr_loader import load_hr
from loaders.entity_resolver import resolve_entities
from seed_reports.generator import generate_all_reports

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    errors: list[str] = []

    # Step 1: init (opens its own driver internally)
    logger.info("=== Step 1/7: init_db ===")
    try:
        init_database()
    except Exception as exc:
        logger.error("init_db FAILED: %s", exc, exc_info=True)
        errors.append(f"init_db: {exc}")

    with open_typedb_driver() as driver:
        steps = [
            ("sales_loader",    load_sales),
            ("finance_loader",  load_finance),
            ("ops_loader",      load_ops),
            ("hr_loader",       load_hr),
            ("entity_resolver", resolve_entities),
            ("seed_reports",    generate_all_reports),
        ]
        for idx, (name, fn) in enumerate(steps, start=2):
            logger.info("=== Step %d/7: %s ===", idx, name)
            try:
                fn(driver)
            except Exception as exc:
                logger.error("%s FAILED: %s", name, exc, exc_info=True)
                errors.append(f"{name}: {exc}")

    if errors:
        logger.error("Run completed with %d error(s):", len(errors))
        for err in errors:
            logger.error("  • %s", err)
        sys.exit(1)
    else:
        logger.info("All steps completed successfully.")


if __name__ == "__main__":
    main()

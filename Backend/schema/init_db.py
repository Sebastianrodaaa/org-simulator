"""
Initialize TypeDB database and load the OrgSim schema.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from typedb.driver import TransactionType

from typedb_util import consume_query_answer, open_typedb_driver

logger = logging.getLogger(__name__)

TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
TYPEDB_DATABASE = os.getenv("TYPEDB_DATABASE", "orgsim")

SCHEMA_FILE = Path(__file__).parent / "orgsim.tql"


def init_database() -> None:
    address = f"{TYPEDB_HOST}:{TYPEDB_PORT}"
    logger.info("Connecting to TypeDB at %s", address)

    with open_typedb_driver() as driver:
        if os.getenv("TYPEDB_INIT_DROP", "").lower() in ("1", "true", "yes"):
            if driver.databases.contains(TYPEDB_DATABASE):
                driver.databases.get(TYPEDB_DATABASE).delete()
                logger.info("Dropped database '%s' (TYPEDB_INIT_DROP)", TYPEDB_DATABASE)
        if not driver.databases.contains(TYPEDB_DATABASE):
            driver.databases.create(TYPEDB_DATABASE)
            logger.info("Created database '%s'", TYPEDB_DATABASE)
        else:
            logger.info("Database '%s' already exists", TYPEDB_DATABASE)

        schema_tql = SCHEMA_FILE.read_text(encoding="utf-8")
        logger.info("Loading schema from %s", SCHEMA_FILE)

        with driver.transaction(TYPEDB_DATABASE, TransactionType.SCHEMA) as tx:
            consume_query_answer(tx.query(schema_tql).resolve())
            tx.commit()
            logger.info("Schema applied successfully")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    init_database()

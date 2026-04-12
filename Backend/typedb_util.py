"""
TypeDB typedb-driver 3.x helpers (no Session API — driver.transaction only).
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from typedb.api.answer.query_answer import QueryAnswer
from typedb.driver import Credentials, DriverOptions, TypeDB, TransactionType

if TYPE_CHECKING:
    from typedb.api.connection.driver import Driver
    from typedb.api.connection.transaction import Transaction

TYPEDB_DATABASE = os.getenv("TYPEDB_DATABASE", "orgsim")


def typedb_address() -> str:
    host = os.getenv("TYPEDB_HOST", "localhost")
    port = int(os.getenv("TYPEDB_PORT", "1729"))
    return f"{host}:{port}"


def typedb_credentials() -> Credentials:
    return Credentials(
        os.getenv("TYPEDB_USER", "admin"),
        os.getenv("TYPEDB_PASSWORD", "password"),
    )


def typedb_driver_options() -> DriverOptions:
    return DriverOptions(is_tls_enabled=False)


def open_typedb_driver():
    """Return TypeDB Core driver context manager (use with ``with``)."""
    address = typedb_address()
    credentials = typedb_credentials()
    options = typedb_driver_options()
    # typedb-driver 3.1+ uses ``TypeDB.driver``; 3.0.x used ``TypeDB.core_driver``.
    connect = getattr(TypeDB, "driver", None) or getattr(TypeDB, "core_driver", None)
    if connect is None:
        raise RuntimeError("typedb-driver missing TypeDB.driver / TypeDB.core_driver")
    return connect(address, credentials, options)


def consume_query_answer(answer: QueryAnswer) -> None:
    """Drain query results so writes / schema defines complete on the server."""
    if answer.is_ok():
        return
    if answer.is_concept_rows():
        for _ in answer.as_concept_rows():
            pass
        return
    if answer.is_concept_documents():
        for _ in answer.as_concept_documents():
            pass
        return


def execute_write_query(tx: Transaction, tql: str) -> None:
    consume_query_answer(tx.query(tql).resolve())


def concept_to_python(concept: object) -> object:
    """Best-effort extract a Python value from a TypeDB Concept."""
    try_get = getattr(concept, "try_get_value", None)
    if callable(try_get):
        v = try_get()
        if v is not None:
            return v
    as_attr = getattr(concept, "as_attribute", None)
    if callable(as_attr):
        try:
            return as_attr().get_value()
        except Exception:
            pass
    return str(concept)


def fetch_rows_read(driver: Driver, database: str, query: str) -> list[dict[str, object]]:
    """Run a read query and return each row as variable name → value."""
    results: list[dict[str, object]] = []
    with driver.transaction(database, TransactionType.READ) as tx:
        qa = tx.query(query).resolve()
        if not qa.is_concept_rows():
            return results
        for row in qa.as_concept_rows():
            row_dict: dict[str, object] = {}
            for var in list(row.column_names()):
                concept = row.get(var)
                if concept is not None:
                    row_dict[var] = concept_to_python(concept)
            results.append(row_dict)
    return results

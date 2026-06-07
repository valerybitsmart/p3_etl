import logging
import pyodbc

logger = logging.getLogger(__name__)


def bulk_insert(conn: pyodbc.Connection, full_table: str, records: list[dict]) -> int:
    if not records:
        return 0

    schema, table = _split_table(full_table)
    cols = list(records[0].keys())
    placeholders = ", ".join("?" * len(cols))
    col_names = ", ".join(f"[{c}]" for c in cols)
    sql = f"INSERT INTO [{schema}].[{table}] ({col_names}) VALUES ({placeholders})"

    rows = [tuple(r.get(c) for c in cols) for r in records]
    cursor = conn.cursor()
    cursor.fast_executemany = True
    cursor.executemany(sql, rows)
    conn.commit()
    logger.debug("Inserted %d rows into [%s].[%s]", len(rows), schema, table)
    return len(rows)


def _split_table(full_name: str) -> tuple[str, str]:
    parts = full_name.strip("[]").replace("[", "").replace("]", "").split(".")
    return (parts[0], parts[1]) if len(parts) == 2 else ("dbo", parts[0])

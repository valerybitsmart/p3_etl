import logging
import pyodbc

logger = logging.getLogger(__name__)

# Priority OData → SQL Server type mapping
_TYPE_MAP = {
    "string":   "NVARCHAR(MAX)",
    "int32":    "INT",
    "int64":    "BIGINT",
    "decimal":  "DECIMAL(18,4)",
    "double":   "FLOAT",
    "boolean":  "BIT",
    "datetime": "DATETIME2",
    "date":     "DATE",
}


def _infer_sql_type(value) -> str:
    if isinstance(value, bool):
        return "BIT"
    if isinstance(value, int):
        return "BIGINT"
    if isinstance(value, float):
        return "FLOAT"
    return "NVARCHAR(MAX)"


def _parse_schema(sample: dict) -> dict[str, str]:
    return {col: _infer_sql_type(val) for col, val in sample.items()}


def _table_exists(conn: pyodbc.Connection, schema: str, table: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?",
        schema, table,
    )
    return cursor.fetchone() is not None


def _split_table(full_name: str) -> tuple[str, str]:
    parts = full_name.strip("[]").replace("[", "").replace("]", "").split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    return "dbo", parts[0]


def ensure_table(conn: pyodbc.Connection, full_table: str, sample: dict) -> None:
    schema, table = _split_table(full_table)
    col_defs = _parse_schema(sample)

    if _table_exists(conn, schema, table):
        _sync_columns(conn, schema, table, col_defs)
    else:
        _create_table(conn, schema, table, col_defs)
    conn.commit()


def _create_table(conn: pyodbc.Connection, schema: str, table: str, col_defs: dict) -> None:
    cols_sql = ",\n    ".join(f"[{col}] {dtype} NULL" for col, dtype in col_defs.items())
    ddl = f"CREATE TABLE [{schema}].[{table}] (\n    {cols_sql}\n)"
    logger.info("Creating table [%s].[%s]", schema, table)
    conn.execute(ddl)


def _sync_columns(conn: pyodbc.Connection, schema: str, table: str, col_defs: dict) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?",
        schema, table,
    )
    existing = {row[0].lower() for row in cursor.fetchall()}
    for col, dtype in col_defs.items():
        if col.lower() not in existing:
            logger.info("Adding column [%s] %s to [%s].[%s]", col, dtype, schema, table)
            conn.execute(f"ALTER TABLE [{schema}].[{table}] ADD [{col}] {dtype} NULL")


def truncate_table(conn: pyodbc.Connection, full_table: str) -> None:
    schema, table = _split_table(full_table)
    logger.info("Truncating [%s].[%s]", schema, table)
    conn.execute(f"TRUNCATE TABLE [{schema}].[{table}]")
    conn.commit()

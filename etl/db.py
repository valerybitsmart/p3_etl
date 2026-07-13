import os
import traceback
import pyodbc
import logging

logger = logging.getLogger(__name__)


def get_connection() -> pyodbc.Connection:
    if os.getenv("SQL_TRUSTED_CONNECTION") == "1":
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.environ['SQL_SERVER']};"
            f"DATABASE={os.environ['SQL_DATABASE']};"
            f"Trusted_Connection=yes;"
        )
    else:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.environ['SQL_SERVER']};"
            f"DATABASE={os.environ['SQL_DATABASE']};"
            f"UID={os.environ['SQL_USERNAME']};"
            f"PWD={os.environ['SQL_PASSWORD']};"
        )
    return pyodbc.connect(conn_str)


def load_tenants(conn: pyodbc.Connection) -> list[dict]:
    """Return all active tenants with their API credentials."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tenant, base_url, auth, description "
        "FROM dbo.etl_tenant_config WHERE active = 1"
    )
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def load_api_config(conn: pyodbc.Connection, tenant: str) -> list[dict]:
    """Return active endpoints for a specific tenant."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, tenant, endpoint, target_table, description "
        "FROM dbo.etl_api_config "
        "WHERE active = 1 AND tenant = ?",
        tenant,
    )
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def load_all_active_endpoints(conn: pyodbc.Connection) -> list[dict]:
    """Return all active endpoints joined with their tenant info."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT c.id, c.tenant, c.endpoint, c.target_table, c.description, "
        "       c.subform_name, c.subform_table, t.base_url, t.auth "
        "FROM dbo.etl_api_config c "
        "JOIN dbo.etl_tenant_config t ON t.tenant = c.tenant "
        "WHERE c.active = 1 AND t.active = 1 "
        "ORDER BY c.tenant, c.endpoint"
    )
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def log_error(
    conn: pyodbc.Connection,
    exc: Exception,
    tenant: str | None = None,
    endpoint: str | None = None,
    target_table: str | None = None,
) -> None:
    """Insert one row into dbo.etl_error_log. Never raises — logging must not crash the caller."""
    try:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        conn.execute(
            "INSERT INTO dbo.etl_error_log "
            "(tenant, endpoint, target_table, error_type, error_message, stack_trace) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            tenant,
            endpoint,
            target_table,
            type(exc).__name__,
            str(exc)[:2000],
            tb,
        )
        conn.commit()
    except Exception:
        logger.exception("Could not write to etl_error_log")


def update_run_stats(conn: pyodbc.Connection, config_id: int, row_count: int) -> None:
    conn.execute(
        "UPDATE dbo.etl_api_config "
        "SET last_run = GETDATE(), last_row_count = ?, updated_at = GETDATE() "
        "WHERE id = ?",
        row_count, config_id,
    )
    conn.commit()

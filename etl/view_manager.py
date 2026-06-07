"""
Auto-generates (or refreshes) unified cross-tenant views.

For every distinct endpoint name (e.g. AGENTS) that has more than one
active tenant table, it creates/replaces a view:

    dbo.v_agents  =  SELECT *, 'tiltan'  AS tenant FROM dbo.tiltan_agents
                     UNION ALL
                     SELECT *, 'nimbos'  AS tenant FROM dbo.nimbos_agents
                     UNION ALL
                     SELECT *, 'a110123' AS tenant FROM dbo.a110123_agents
"""
import logging
import pyodbc

logger = logging.getLogger(__name__)


def refresh_views(conn: pyodbc.Connection) -> list[str]:
    """
    Rebuild all unified views based on the current etl_api_config.
    Returns the list of view names that were created/updated.
    """
    cursor = conn.cursor()

    # All active endpoint → table mappings grouped by endpoint name
    cursor.execute(
        "SELECT c.endpoint, c.target_table, c.tenant "
        "FROM dbo.etl_api_config c "
        "JOIN dbo.etl_tenant_config t ON t.tenant = c.tenant "
        "WHERE c.active = 1 AND t.active = 1 "
        "ORDER BY c.endpoint, c.tenant"
    )
    rows = cursor.fetchall()

    # Group by endpoint
    grouped: dict[str, list[tuple[str, str]]] = {}
    for endpoint, table, tenant in rows:
        grouped.setdefault(endpoint, []).append((tenant, table))

    created: list[str] = []
    for endpoint, entries in grouped.items():
        view_name = f"dbo.v_{endpoint.lower()}"
        _create_or_alter_view(conn, view_name, entries)
        created.append(view_name)

    return created


def _table_exists(conn: pyodbc.Connection, schema: str, table: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?",
        schema, table,
    )
    return cursor.fetchone() is not None


def _create_or_alter_view(
    conn: pyodbc.Connection,
    view_name: str,
    entries: list[tuple[str, str]],   # [(tenant, full_table), ...]
) -> None:
    # Only include entries whose underlying table actually exists
    valid = []
    for tenant, full_table in entries:
        parts = full_table.strip("[]").replace("[", "").replace("]", "").split(".")
        schema, table = (parts[0], parts[1]) if len(parts) == 2 else ("dbo", parts[0])
        if _table_exists(conn, schema, table):
            valid.append((tenant, full_table))
        else:
            logger.warning("Skipping %s from view %s - table does not exist yet", full_table, view_name)

    if not valid:
        logger.info("No tables ready for view %s - skipping", view_name)
        return

    union_parts = [
        f"SELECT *, '{tenant}' AS tenant FROM {full_table}"
        for tenant, full_table in valid
    ]
    union_sql = "\n    UNION ALL\n    ".join(union_parts)

    schema_name, view_bare = _split_view(view_name)

    # pyodbc cannot run multiple statements in one execute() call.
    # Split into DROP (if exists) + CREATE - two separate round-trips.
    drop_ddl = (
        f"IF OBJECT_ID('[{schema_name}].[{view_bare}]', 'V') IS NOT NULL "
        f"DROP VIEW [{schema_name}].[{view_bare}]"
    )
    create_ddl = (
        f"CREATE VIEW [{schema_name}].[{view_bare}] AS\n"
        f"    {union_sql}"
    )

    logger.info("Refreshing view %s (tenants: %s)", view_name, [t for t, _ in valid])
    conn.execute(drop_ddl)
    conn.execute(create_ddl)
    conn.commit()


def _split_view(full_name: str) -> tuple[str, str]:
    parts = full_name.strip("[]").replace("[", "").replace("]", "").split(".")
    return (parts[0], parts[1]) if len(parts) == 2 else ("dbo", parts[0])

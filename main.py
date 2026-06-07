#!/usr/bin/env python3
"""
Priority → SQL Server ETL entry point.

Usage:
    python main.py                              # all active tenants + endpoints
    python main.py --tenant tiltan              # one tenant, all its endpoints
    python main.py --endpoint AGENTS            # one endpoint across all tenants
    python main.py --tenant tiltan --endpoint AGENTS  # exact single job
"""
import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from etl.api_client import fetch_all
from etl.db import get_connection, load_all_active_endpoints, log_error, update_run_stats
from etl.loader import bulk_insert
from etl.notify import alert_errors, alert_no_endpoints, alert_success
from etl.table_manager import ensure_table, truncate_table
from etl.view_manager import refresh_views

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)-8s %(name)s - %(message)s",
    handlers=[logging.StreamHandler(stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False))],
)
logger = logging.getLogger("etl.main")


def run_endpoint(conn, cfg: dict) -> int:
    """
    Load one tenant/endpoint combination.
    cfg keys: id, tenant, endpoint, target_table, base_url, auth
    Returns row count. Raises on failure.
    """
    tenant   = cfg["tenant"]
    endpoint = cfg["endpoint"]
    table    = cfg["target_table"]
    logger.info("=== [%s] %s -> %s ===", tenant, endpoint, table)

    total = 0
    first_page = True

    for page in fetch_all(cfg["base_url"], cfg["auth"], endpoint):
        if first_page:
            ensure_table(conn, table, page[0])
            truncate_table(conn, table)
            first_page = False

        total += bulk_insert(conn, table, page)
        logger.info("  [%s/%s] loaded %d rows (total: %d)", tenant, endpoint, len(page), total)

    update_run_stats(conn, cfg["id"], total)
    logger.info("=== [%s] %s done - %d rows ===", tenant, endpoint, total)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Priority ETL")
    parser.add_argument("--tenant",   help="Run only this tenant (e.g. tiltan)")
    parser.add_argument("--endpoint", help="Run only this endpoint (e.g. AGENTS)")
    args = parser.parse_args()

    conn = get_connection()

    configs = load_all_active_endpoints(conn)

    # Apply CLI filters
    if args.tenant:
        configs = [c for c in configs if c["tenant"].lower() == args.tenant.lower()]
    if args.endpoint:
        configs = [c for c in configs if c["endpoint"].upper() == args.endpoint.upper()]

    if not configs:
        logger.warning("No active endpoints matched the given filters")
        alert_no_endpoints()
        conn.close()
        return

    successes: list[dict] = []
    errors:    list[dict] = []

    for cfg in configs:
        try:
            rows = run_endpoint(conn, cfg)
            successes.append({
                "endpoint": cfg["endpoint"],
                "tenant":   cfg["tenant"],
                "table":    cfg["target_table"],
                "rows":     rows,
            })
        except Exception as exc:
            logger.exception("Failed [%s/%s]", cfg["tenant"], cfg["endpoint"])
            log_error(conn, exc, cfg["tenant"], cfg["endpoint"], cfg["target_table"])
            errors.append({"tenant": cfg["tenant"], "endpoint": cfg["endpoint"], "exc": exc})

    # Rebuild unified views after all loads
    if successes:
        try:
            views = refresh_views(conn)
            logger.info("Views refreshed: %s", views)
        except Exception as exc:
            logger.exception("Failed to refresh views (data was loaded successfully)")
            log_error(conn, exc, tenant=None, endpoint="VIEW_REFRESH", target_table=None)

        alert_success(successes)

    if errors:
        alert_errors(errors)

    conn.close()

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()

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
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from etl.api_client import fetch_all
from etl.db import get_connection, load_all_active_endpoints, log_error, update_run_stats
from etl.loader import bulk_insert
from etl.notify import alert_errors, alert_no_endpoints, alert_success
from etl.table_manager import ensure_table, truncate_table
from etl.view_manager import refresh_views

def _setup_logging() -> None:
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"run_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

    fmt = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
    level = os.getenv("LOG_LEVEL", "INFO")

    handlers: list[logging.Handler] = [
        logging.StreamHandler(
            stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
        ),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]
    logging.basicConfig(level=level, format=fmt, handlers=handlers)
    logging.getLogger("etl.main").info("Log file: %s", log_file)

_setup_logging()
logger = logging.getLogger("etl.main")


def run_endpoint(conn, cfg: dict) -> int:
    """
    Load one tenant/endpoint combination, optionally expanding a subform.
    Returns parent row count. Raises on failure.
    """
    tenant        = cfg["tenant"]
    endpoint      = cfg["endpoint"]
    table         = cfg["target_table"]
    subform_name  = cfg.get("subform_name")   # e.g. 'FNCITEMS_SUBFORM'
    subform_table = cfg.get("subform_table")  # e.g. 'dbo.tiltan_fncitems'

    if subform_name:
        logger.info("=== [%s] %s (expand: %s) ===", tenant, endpoint, subform_name)
    else:
        logger.info("=== [%s] %s -> %s ===", tenant, endpoint, table)

    total_parent  = 0
    total_subform = 0
    first_page    = True

    for page in fetch_all(cfg["base_url"], cfg["auth"], endpoint, expand=subform_name):
        if first_page:
            # Strip subform key from parent sample before schema inference
            parent_sample = {k: v for k, v in page[0].items() if k != subform_name}
            ensure_table(conn, table, parent_sample)
            truncate_table(conn, table)
            if subform_name and subform_table:
                # Gather a non-empty subform sample across the first page
                subform_sample = next(
                    (
                        {k: v for k, v in row.items() if not isinstance(v, (dict, list))}
                        for rec in page
                        for row in (rec.get(subform_name) or [])
                    ),
                    None,
                )
                if subform_sample:
                    ensure_table(conn, subform_table, subform_sample)
                    truncate_table(conn, subform_table)
            first_page = False

        # Separate parent rows from subform rows
        parent_rows  = [{k: v for k, v in rec.items() if k != subform_name} for rec in page]
        total_parent += bulk_insert(conn, table, parent_rows)

        if subform_name and subform_table:
            subform_rows = [
                {k: v for k, v in row.items() if not isinstance(v, (dict, list))}
                for rec in page
                for row in (rec.get(subform_name) or [])
            ]
            total_subform += bulk_insert(conn, subform_table, subform_rows)

        logger.info(
            "  [%s/%s] parent: %d rows | subform: %d rows",
            tenant, endpoint, total_parent, total_subform,
        )

    update_run_stats(conn, cfg["id"], total_parent)
    logger.info(
        "=== [%s] %s done - parent: %d rows, subform: %d rows ===",
        tenant, endpoint, total_parent, total_subform,
    )
    return total_parent


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

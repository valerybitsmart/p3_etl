import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

_WHAPI_URL = "https://gate.whapi.cloud/messages/text"


def _recipients() -> list[str]:
    """
    Read WHAPI_RECIPIENT (comma-separated) from .env.
    Each entry is a bare phone number or a full whapi address.
      e.g.  972501234567, 972509876543
      or    972501234567@s.whatsapp.net, 972509876543@s.whatsapp.net
    """
    raw = os.environ.get("WHAPI_RECIPIENT", "")
    numbers = [r.strip() for r in raw.split(",") if r.strip()]
    return [n if "@" in n else f"{n}@s.whatsapp.net" for n in numbers]


def _send(text: str) -> None:
    token = os.environ.get("WHAPI_TOKEN")
    recipients = _recipients()

    if not token or not recipients:
        logger.warning("WhatsApp alerts not configured (WHAPI_TOKEN / WHAPI_RECIPIENT missing)")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for recipient in recipients:
        try:
            resp = requests.post(
                _WHAPI_URL,
                json={"to": recipient, "body": text},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            logger.debug("WhatsApp alert sent to %s (status %s)", recipient, resp.status_code)
        except Exception:
            logger.exception("Failed to send WhatsApp alert to %s", recipient)


def alert_success(results: list[dict]) -> None:
    """results: list of {"tenant": str, "endpoint": str, "table": str, "rows": int}"""
    lines = [f"✅ *Priority ETL — SUCCESS* ({_now()})"]
    # Group output by tenant for readability
    tenants: dict[str, list[dict]] = {}
    for r in results:
        tenants.setdefault(r["tenant"], []).append(r)
    for tenant, items in tenants.items():
        lines.append(f"\n*{tenant}*")
        for r in items:
            lines.append(f"  • {r['endpoint']} → `{r['table']}` : {r['rows']:,} rows")
    _send("\n".join(lines))


def alert_errors(errors: list[dict]) -> None:
    """
    Send one combined error message.
    errors: list of {"tenant": str, "endpoint": str, "exc": Exception}
    """
    lines = [f"❌ *P3 Priority ETL — ERRORS* ({_now()})"]
    # Group by tenant
    tenants: dict[str, list[dict]] = {}
    for e in errors:
        tenants.setdefault(e["tenant"], []).append(e)
    for tenant, items in tenants.items():
        lines.append(f"\n*{tenant}* tables failed:")
        for e in items:
            lines.append(f"  • {e['endpoint']} - {_short_reason(e['exc'])}")
    _send("\n".join(lines))


def _short_reason(exc: Exception) -> str:
    """Return a one-liner reason: HTTP status code if available, else exception type."""
    import requests
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return f"code {exc.response.status_code}"
    return type(exc).__name__


def alert_no_endpoints() -> None:
    _send(f"⚠️ *Priority ETL* ({_now()})\nNo active endpoints found in etl_api_config.")


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

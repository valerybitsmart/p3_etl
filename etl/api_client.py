import logging
import os
from typing import Generator

import requests
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def _cfg_int(key: str, default: int) -> int:
    return int(os.getenv(key, default))


def _make_session(auth: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": auth})
    return session


def _get(session: requests.Session, url: str, params: dict | None = None) -> dict:
    attempts  = _cfg_int("API_RETRY_ATTEMPTS", 3)
    wait_min  = _cfg_int("API_RETRY_WAIT_MIN", 2)
    wait_max  = _cfg_int("API_RETRY_WAIT_MAX", 30)
    timeout   = (
        _cfg_int("API_CONNECT_TIMEOUT", 10),
        _cfg_int("API_READ_TIMEOUT", 300),
    )

    @retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _call() -> dict:
        resp = session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    return _call()



def fetch_all(
    base_url: str,
    auth: str,
    endpoint: str,
    expand: str | None = None,
) -> Generator[list[dict], None, None]:
    """
    Yield pages of records from a Priority OData endpoint.

    Args:
        base_url:  Tenant base URL, e.g. https://.../tiltan
        auth:      Authorization header value, e.g. 'Basic ABC123=='
        endpoint:  OData entity name, e.g. 'FNCTRANS'
        expand:    Optional OData $expand subform, e.g. 'FNCITEMS_SUBFORM'
    """
    session = _make_session(auth)
    url = f"{base_url.rstrip('/')}/{endpoint}"
    batch = _cfg_int("BATCH_SIZE", 1000)

    params: dict = {"$top": batch, "$skip": 0}
    if expand:
        params["$expand"] = expand

    page_num = 0
    while True:
        data = _get(session, url, params)
        records = data.get("value", [])
        if not records:
            break

        page_num += 1
        yield records
        if len(records) < batch:
            break
        params["$skip"] += batch

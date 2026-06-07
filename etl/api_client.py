import logging
import os
from typing import Generator

import requests
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def _make_session(auth: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": auth})
    return session


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _get(session: requests.Session, url: str, params: dict | None = None) -> dict:
    resp = session.get(url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_all(base_url: str, auth: str, endpoint: str) -> Generator[list[dict], None, None]:
    """
    Yield pages of records from a Priority OData endpoint.

    Args:
        base_url:  Tenant base URL, e.g. https://.../tiltan
        auth:      Authorization header value, e.g. 'Basic ABC123=='
        endpoint:  OData entity name, e.g. 'AGENTS'
    """
    session = _make_session(auth)
    url = f"{base_url.rstrip('/')}/{endpoint}"
    batch = int(os.getenv("BATCH_SIZE", 1000))

    params: dict = {"$top": batch, "$skip": 0}
    while True:
        data = _get(session, url, params)
        records = data.get("value", [])
        if not records:
            break
        yield records
        if len(records) < batch:
            break
        params["$skip"] += batch

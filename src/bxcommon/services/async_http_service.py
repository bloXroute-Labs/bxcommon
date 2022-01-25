from typing import Optional, Dict, Any

import aiohttp

from bxcommon import constants
from bxcommon.services import http_service
from bxcommon.services.http_service import JT
from bxutils import logging, log_messages
from bxutils.encoding import json_encoder

logger = logging.get_logger(__name__)

_session: Optional[aiohttp.ClientSession] = None


async def initialize():
    # pylint: disable=global-statement
    global _session
    _session = aiohttp.ClientSession()


async def close():
    session = _session
    if session is not None:
        await session.close()


async def get(endpoint: str, **kwargs) -> Optional[JT]:
    return await request("GET", endpoint, **kwargs)


async def get_with_payload(endpoint: str, payload: Dict[str, Any]) -> Optional[JT]:
    return await get(endpoint, data=json_encoder.to_json(payload))


async def request(method: str, endpoint: str, **kwargs) -> Optional[JT]:
    ssl_context = http_service.ssl_context()
    assert ssl_context is not None

    session = _session
    assert session is not None

    url = http_service.build_url(endpoint)
    async with session.request(
        method,
        url,
        headers=constants.HTTP_HEADERS,
        ssl=ssl_context,
        timeout=constants.HTTP_REQUEST_TIMEOUT,
        **kwargs,
    ) as response:
        try:
            return await response.json()
        except Exception as e:  # pylint: disable=broad-except
            logger.error(log_messages.HTTP_REQUEST_RETURNED_ERROR, method, url, e)
            return None

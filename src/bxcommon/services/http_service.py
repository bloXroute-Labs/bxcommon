import status
import json
from typing import Optional, Dict, Any, Union, List
from urllib3 import Retry, HTTPResponse
from urllib3.exceptions import HTTPError
from urllib3.poolmanager import PoolManager
from urllib3.util import parse_url
from ssl import SSLContext

from bxcommon.utils import json_utils
from bxutils import logging
from bxcommon import constants

# recursive types are not supported: https://github.com/python/typing/issues/182

jsonT = Union[Dict[str, Any], List[Any]]

logger = logging.get_logger(__name__)

_url = constants.SDN_ROOT_URL
http_pool_manager: PoolManager = PoolManager()


def set_root_url(sdn_url: str, ssl_context: Optional[SSLContext] = None):
    global _url
    _url = sdn_url
    reset_pool(ssl_context)


def reset_pool(ssl_context: Optional[SSLContext] = None):
    global http_pool_manager
    url = parse_url(_url)
    http_pool_manager = PoolManager(
        num_pools=constants.THREAD_POOL_WORKER_COUNT,
        host=url.host,
        port=url.port,
        retries=Retry(
            connect=constants.HTTP_REQUEST_RETRIES_COUNT,
            read=constants.HTTP_REQUEST_RETRIES_COUNT,
            redirect=constants.HTTP_REQUEST_RETRIES_COUNT,
            backoff_factor=constants.HTTP_REQUEST_BACKOFF_FACTOR
        ),
        ssl_context=ssl_context,
        assert_hostname=False
    )


def post_json(endpoint: str, payload=None) -> Optional[jsonT]:
    return _http_request("POST", endpoint, body=json_utils.serialize(payload),
                         headers=constants.HTTP_HEADERS)


def patch_json(endpoint: str, payload=None) -> Optional[jsonT]:
    return _http_request("PATCH", endpoint, body=json_utils.serialize(payload),
                         headers=constants.HTTP_HEADERS)


def delete_json(endpoint: str, payload=None) -> Optional[jsonT]:
    return _http_request("DELETE", endpoint, body=json_utils.serialize(payload),
                         headers=constants.HTTP_HEADERS)


def get_json(endpoint: str) -> Optional[jsonT]:
    return _http_request("GET", endpoint,
                         headers=constants.HTTP_HEADERS)


def build_url(endpoint: str) -> str:
    if not endpoint or not isinstance(endpoint, str):
        raise ValueError("Missing or invalid URL")
    return _url + endpoint


def raise_for_status(res: HTTPResponse) -> None:
    if status.is_client_error(res.status) or status.is_server_error(res.status):
        raise HTTPError("{}:{}", res.status, res.reason)


def _http_request(method: str,
                  endpoint: str,
                  **kwargs) -> Optional[jsonT]:
    url = build_url(endpoint)
    try:
        logger.trace("HTTP {0} to {1}", method, url)
        response = http_pool_manager.request(
            method=method,
            url=url,
            timeout=constants.HTTP_REQUEST_TIMEOUT,
            **kwargs)
        raise_for_status(response)
    except Exception as e:
        logger.error("{0} to {1} returned error: {2}", method, url, e)
        return None

    return json.loads(response.data)

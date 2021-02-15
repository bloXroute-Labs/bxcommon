import json
from ssl import SSLContext
from typing import Optional, Dict, Any, Union, List

import status
from urllib3 import Retry, HTTPResponse
from urllib3.exceptions import HTTPError, MaxRetryError
from urllib3.poolmanager import PoolManager
from urllib3.util import parse_url

from bxcommon import constants
from bxutils import log_messages
from bxutils import logging
from bxutils.encoding import json_encoder

# recursive types are not supported: https://github.com/python/typing/issues/182

JT = Union[Dict[str, Any], List[Any]]

logger = logging.get_logger(__name__)

_url = constants.SDN_ROOT_URL
_ssl_context: Optional[SSLContext] = None

METHODS_WHITELIST = frozenset(
    ["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST", "PATCH"]
)


def set_root_url(sdn_url: str, ssl_context: Optional[SSLContext] = None):
    # pylint: disable=global-statement
    global _url
    _url = sdn_url
    update_http_ssl_context(ssl_context)


def update_http_ssl_context(ssl_context: Optional[SSLContext] = None):
    # pylint: disable=global-statement
    global _ssl_context
    _ssl_context = ssl_context


def post_json(endpoint: str, payload=None) -> Optional[JT]:
    return _http_request(
        "POST",
        endpoint,
        False,
        body=json_encoder.to_json(payload),
        headers=constants.HTTP_HEADERS
    )


def patch_json(endpoint: str, payload=None) -> Optional[JT]:
    return _http_request(
        "PATCH",
        endpoint,
        False,
        body=json_encoder.to_json(payload),
        headers=constants.HTTP_HEADERS
    )


def delete_json(endpoint: str, payload=None) -> Optional[JT]:
    return _http_request(
        "DELETE",
        endpoint,
        False,
        body=json_encoder.to_json(payload),
        headers=constants.HTTP_HEADERS
    )


def get_json(endpoint: str) -> Optional[JT]:
    return _http_request(
        "GET",
        endpoint,
        False,
        headers=constants.HTTP_HEADERS
    )


def get_json_raising_timeout(endpoint: str) -> Optional[JT]:
    return _http_request(
        "GET",
        endpoint,
        True,
        headers=constants.HTTP_HEADERS
    )


def get_json_with_payload(endpoint: str, payload=None) -> Optional[JT]:
    return _http_request(
        "GET",
        endpoint,
        False,
        body=json_encoder.to_json(payload),
        headers=constants.HTTP_HEADERS
    )


def build_url(endpoint: str) -> str:
    if not endpoint or not isinstance(endpoint, str):
        raise ValueError("Missing or invalid URL")
    return _url + endpoint


def raise_for_status(res: HTTPResponse) -> None:
    if status.is_client_error(res.status) or status.is_server_error(res.status):
        raise HTTPError(f"{res.status}:{res.reason}")


def _http_request(
    method: str, endpoint: str, handle_timeout: bool, **kwargs
) -> Optional[JT]:
    url = build_url(endpoint)
    parsed_url = parse_url(url)
    pm_args = {
        "num_pools": constants.HTTP_POOL_MANAGER_COUNT,
        "host": parsed_url.host,
        "port": parsed_url.port,
        "retries": Retry(
            connect=constants.HTTP_REQUEST_RETRIES_COUNT,
            read=constants.HTTP_REQUEST_RETRIES_COUNT,
            redirect=constants.HTTP_REQUEST_RETRIES_COUNT,
            backoff_factor=constants.HTTP_REQUEST_BACKOFF_FACTOR,
            method_whitelist=METHODS_WHITELIST
        ),
        "ssl_context": _ssl_context,
    }
    if _ssl_context is not None and url.startswith("https"):
        pm_args["assert_hostname"] = False
    http_pool_manager: PoolManager = PoolManager(**pm_args)
    try:
        logger.trace("HTTP {0} to {1}", method, url)
        response = http_pool_manager.request(
            method=method,
            url=parsed_url.url,
            timeout=constants.HTTP_REQUEST_TIMEOUT,
            **kwargs
        )
        raise_for_status(response)
    except MaxRetryError as e:
        logger.info("{} to {} failed due to: {}.", method, url, e)
        return None
    except TimeoutError:
        if handle_timeout:
            raise TimeoutError
        return None
    except Exception as e:  # pylint: disable=broad-except
        logger.error(log_messages.HTTP_REQUEST_RETURNED_ERROR, method, url, e)
        return None

    return json.loads(response.data)

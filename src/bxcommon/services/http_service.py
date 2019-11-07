from requests import HTTPError, RequestException, Session
from requests.adapters import Retry, HTTPAdapter
from typing import Optional, Dict, Any, Union, List

from bxutils import logging

from bxcommon import constants
from bxcommon.utils import json_utils

logger = logging.get_logger(__name__)

# recursive types are not supported: https://github.com/python/typing/issues/182
jsonT = Union[Dict[str, Any], List[Any]]


_sdn_url = constants.SDN_ROOT_URL
_http_adapter = HTTPAdapter(max_retries=Retry(
    total=constants.HTTP_REQUEST_RETRIES_COUNT,
    connect=constants.HTTP_REQUEST_RETRIES_COUNT,
    read=constants.HTTP_REQUEST_RETRIES_COUNT,
    redirect=constants.HTTP_REQUEST_RETRIES_COUNT,
    backoff_factor=constants.HTTP_REQUEST_BACKOFF_FACTOR
))
_http = Session()


def set_sdn_url(sdn_url: str):
    global _sdn_url
    _sdn_url = sdn_url
    _http.mount(_sdn_url, adapter=_http_adapter)


def build_url(endpoint: str) -> str:
    if not endpoint or not isinstance(endpoint, str):
        raise ValueError("Missing or invalid URL")
    return _sdn_url + endpoint


def _http_request(method: str, endpoint: str, **kwargs) -> Optional[jsonT]:
    url = build_url(endpoint)
    try:
        logger.trace("HTTP {0} to {1}", method, url)
        response = _http.request(method=method, url=url, timeout=constants.HTTP_REQUEST_TIMEOUT, **kwargs)
        response.raise_for_status()
    except HTTPError as e:
        logger.error("{0} to {1} returned error: {2}", method, url, e)
        return None
    except RequestException as e:
        logger.error("{0} to {1} failed with error: {2}", method, url, e)
        return None

    return response.json()


def get_json(endpoint: str) -> Optional[jsonT]:
    return _http_request("GET", endpoint)


def post_json(endpoint: str, payload=None) -> Optional[jsonT]:
    return _http_request("POST", endpoint, data=json_utils.serialize(payload),
                         headers={"Content-Type": "application/json"})


def patch_json(endpoint: str, payload=None) -> Optional[jsonT]:
    return _http_request("PATCH", endpoint, data=json_utils.serialize(payload),
                         headers={"Content-Type": "application/json"})


def delete_json(endpoint: str, payload=None) -> Optional[jsonT]:
    return _http_request("DELETE", endpoint, data=json_utils.serialize(payload),
                         headers={"Content-Type": "application/json"})

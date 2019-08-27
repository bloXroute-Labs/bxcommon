import requests
from requests import HTTPError, RequestException
from typing import Optional, Dict, Any, Union, List

from bxcommon import constants
from bxcommon.utils import logger, json_utils

# recursive types are not supported: https://github.com/python/typing/issues/182
jsonT = Union[Dict[str, Any], List[Any]]


def build_url(endpoint: str) -> str:
    if not endpoint or not isinstance(endpoint, str):
        raise ValueError("Missing or invalid URL")
    return constants.SDN_ROOT_URL + endpoint


def _http_request(method: str, endpoint: str, **kwargs) -> Optional[jsonT]:
    url = build_url(endpoint)
    try:
        logger.debug("HTTP {0} to {1}".format(method, url))
        response = requests.request(method=method, url=url, **kwargs)
        response.raise_for_status()
    except HTTPError as e:
        logger.error("{0} to {1} returned error: {2}".format(method, url, e))
        return None
    except RequestException as e:
        logger.error("{0} to {1} failed with error: {2}".format(method, url, e))
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

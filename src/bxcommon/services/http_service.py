import json

import requests
from requests import HTTPError, RequestException

from bxcommon import constants
from bxcommon.utils import logger
from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def build_url(endpoint):
    if not endpoint or not isinstance(endpoint, str):
        raise ValueError("Missing or invalid URL")
    return constants.SDN_ROOT_URL + endpoint


def _http_request(method, endpoint, **kwargs):
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


def get_json(endpoint):
    return _http_request("GET", endpoint)


def post_json(endpoint, payload=None):
    return _http_request("POST", endpoint, data=json.dumps(payload, cls=ClassJsonEncoder),
                         headers={"Content-Type": "application/json"})


def patch_json(endpoint, payload=None):
    return _http_request("PATCH", endpoint, data=json.dumps(payload, cls=ClassJsonEncoder),
                         headers={"Content-Type": "application/json"})


def delete_json(endpoint, payload=None):
    return _http_request("DELETE", endpoint, data=json.dumps(payload, cls=ClassJsonEncoder),
                         headers={"Content-Type": "application/json"})

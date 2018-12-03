import json

import requests
from requests import HTTPError, RequestException

from bxcommon.utils import logger
from bxcommon.utils.class_json_encoder import ClassJsonEncoder
from bxcommon import constants


def build_url(url):
    if not url or not isinstance(url, str):
        raise ValueError("Missing or invalid URL")
    return constants.BX_API_ROOT_URL + url


def _http_request(method, url, **kwargs):
    endpoint = build_url(url)
    try:
        logger.debug("HTTP {0} to {1}".format(method, endpoint))
        response = requests.request(method=method, url=endpoint, **kwargs)
        response.raise_for_status()
    except HTTPError as e:
        logger.error("{0} to {1} returned error: {1}".format(method, endpoint, e))
        return None
    except RequestException as e:
        logger.error("{0} to {1} failed with error: {1}".format(method, endpoint, e))
        return None

    return response.json()


def get_json(url):
    return _http_request(method='GET', url=url)


def post_json(url, payload=None):
    return _http_request(method='POST', url=url, data=json.dumps(payload, cls=ClassJsonEncoder),
                         headers={'Content-Type': 'application/json'})

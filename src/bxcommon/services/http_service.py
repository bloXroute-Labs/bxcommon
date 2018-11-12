import json

import requests
from requests import HTTPError, RequestException

from bxcommon.utils import logger
from bxcommon.utils.class_json_encoder import ClassJsonEncoder


def get_json(url):
    if not url or not isinstance(url, str):
        raise ValueError("Missing or invalid URL")

    try:
        logger.debug("HTTP GET to {}".format(url))

        response = requests.get(url)
        response.raise_for_status()
    except HTTPError as e:
        logger.debug("GET to {0} returned error: {1}".format(url, e))
        return None
    except RequestException as e:
        logger.debug("GET to {0} failed with error: {1}".format(url, e))
        return None

    return response.json()


def post_json(url, payload=None):
    if not url or not isinstance(url, str):
        raise ValueError("Missing or invalid URL")

    try:
        logger.debug("HTTP POST to {}".format(url))

        response = requests.post(url, data=json.dumps(payload, cls=ClassJsonEncoder),
                                 headers={'Content-Type': 'application/json'})
        response.raise_for_status()
    except HTTPError as e:
        logger.debug("POST to {0} returned error: {1}".format(url, e))
        return None
    except RequestException as e:
        logger.debug("POST to {0} failed with error: {1}".format(url, e))
        return None

    return response.json()

import requests
from requests import HTTPError, RequestException

from bxcommon.utils import logger


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


def post_json(url, json=None):
    if not url or not isinstance(url, str):
        raise ValueError("Missing or invalid URL")

    try:
        logger.debug("HTTP POST to {}".format(url))

        response = requests.post(url, json=json)
        response.raise_for_status()
    except HTTPError as e:
        logger.debug("POST to {0} returned error: {1}".format(url, e))
        return None
    except RequestException as e:
        logger.debug("POST to {0} failed with error: {1}".format(url, e))
        return None

    return response.json()

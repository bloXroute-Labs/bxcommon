import os
import re
import socket
import time
import configparser
from typing import Optional

from requests import get
from bxcommon import constants
from bxcommon.utils import logger


def blocking_resolve_ip(net_address):
    if not net_address:
        raise ValueError("Missing network address.")

    tries = 0
    resolved_ip = None
    while resolved_ip is None:
        try:
            resolved_ip = socket.gethostbyname(net_address)
        except socket.error:
            time.sleep(constants.NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS)
            resolved_ip = None
            tries += 1

            # logger might not yet be initialized
            print("Unable to connect to address {0}. Retried {1}".format(net_address, tries))

            if tries >= constants.NET_ADDR_INIT_CONNECT_TRIES:
                raise EnvironmentError("Unable to resolve address {}.".format(net_address))

    return resolved_ip


def blocking_resolve_peers(peer_models):
    if not peer_models:
        return

    for peer in peer_models:
        resolved_ip = blocking_resolve_ip(peer.ip)

        if peer.ip != resolved_ip:
            logger.debug("Resolved peer {0} to {1}".format(peer.ip, resolved_ip))
            peer.ip = resolved_ip

    logger.debug("Resolved peers successfully.")


# Configure the global logger.
def init_logging(log_path, to_stdout=True):
    """
    Configure global logger.
    """
    log_path = log_path
    logger.log_init(log_path, to_stdout)


def log_pid(file_name):
    """
    Capture process id for easy termination in multi-thread scenarios.
    """
    with open(file_name, "w") as writable_file:
        writable_file.write(str(os.getpid()))


def get_node_public_ip() -> str:
    """
    Get the public IP address of the node based on a request to `PUBLIC_IP_ADDR_RESOLVER`. If address cannot be
    resolved, it must be specified as a command line argument

    :return: the resolved IP address
    """
    try:
        get_response = get(constants.PUBLIC_IP_ADDR_RESOLVER).text
        public_ip_addr = re.findall(constants.PUBLIC_IP_ADDR_REGEX, get_response)
        if public_ip_addr:
            return public_ip_addr[0]

        raise ConnectionError("Unable to parse IP from response - response was [{}]".format(get_response))
    except ConnectionError as conn_err:
        # logger might not yet be initialized
        print("Unable to determine public IP address, please specify one manually via the command line arguments.\n\n"
              "Detailed error message:\n\t{}".format(conn_err))
        exit(1)


def get_env_default(key: str) -> str:
    """
    Read the default values for given key from the config file for a specific environment. The environment is stored
    in the hosts environment variables as `BLXR_ENV=local` for example. If the environment isn't set or doesn't exist
    in the config file, the global default values are returned

    :param key: the key to get the env default values for
    :return: the env default value
    """
    config = configparser.ConfigParser()
    config.read(constants.NODE_CONFIG_PATH)

    # If the environment var itself does not exist, return the global default value for the key
    if constants.BLXR_ENV_VAR not in os.environ:
        return config.defaults()[key]

    environment = os.environ[constants.BLXR_ENV_VAR].lower()

    # If the given environment var does not have an entry in the config file, return the global default
    if environment in config.sections():
        return config.get(environment, key)
    else:
        return config.defaults()[key]

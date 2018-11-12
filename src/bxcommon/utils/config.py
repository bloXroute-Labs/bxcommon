import os
import socket
import time

from bxcommon.constants import NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS, NET_ADDR_INIT_CONNECT_TRIES
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
            time.sleep(NET_ADDR_INIT_CONNECT_RETRY_INTERVAL_SECONDS)
            resolved_ip = None
            tries += 1
            logger.debug("Unable to connect to address {0}. Retried {1}".format(net_address, tries))

            if tries >= NET_ADDR_INIT_CONNECT_TRIES:
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
    log_path = log_path
    logger.log_init(log_path, to_stdout)


# Capture the process id for easy termination in multi-thread scenarios.
def log_pid(file_name):
    with open(file_name, "w") as writable_file:
        writable_file.write(str(os.getpid()))

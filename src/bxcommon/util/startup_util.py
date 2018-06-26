import ConfigParser
import argparse
import os
import socket
import time

# Some websites are blocked in certain jurisdictions, so we try multiple websites to see whichever one works.
from bxcommon import utils

# TODO much of this needs to be refactored into a config loader that
# TODO   consumes args/files and returns a standard config

# FIXME we need to move away from these external checks
WEBSITES_TO_TRY = ['www.google.com', 'www.alibaba.com']

ALL_PARAMS = [
    'my_ip',
    'my_port',
    'peers',
    'my_idx',
    'manager_idx',
    'log_path',
    'log_stdout'
]


# Capture the process id for easy termination in multi-thread scenarios.
def log_pid(file_name):
    with open(file_name, "w") as f:
        f.write(str(os.getpid()))


# Returns the local internal IP address of the node.
# If the node is behind a NAT or proxy, then this is not the externally visible IP address.
def get_my_ip():
    for website in WEBSITES_TO_TRY:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((website, 80))
            return s.getsockname()[0]
        except socket.timeout:
            continue

    raise Exception("Could not find any local name!")


# Parse the config filename and return a params dictionary with the params from ALL_PARAMS and extras
def parse_config_file(filename, localname, extra_params=None):
    client_config = ConfigParser.ConfigParser()
    client_config.read(filename)

    params = ALL_PARAMS
    if extra_params:
        params += extra_params

    config_params = {}
    for param_name in params:
        config_params[param_name] = getparam(client_config, localname, param_name)

    return client_config, config_params


# Gets the param "pname" from the config file.
# If the param exists under the localname, we use that one. Otherwise, we use
# the param under default.
def getparam(client_config, local_name, param_name):
    if not client_config:
        return None

    try:
        return client_config.get(local_name, param_name)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        try:
            return client_config.get("default", param_name)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            return None


# Parse the peers file and returns a dictionary of {cls : list of ip, port pairs}
# to tell the node which connection types to instantiate.
# Parse the peers string and return two lists:
#   1) A list of relays that are internal nodes in our network
#   2) A list of trusted peers that we will connect to.
def parse_peers(peers_string):
    nodes = {}

    if peers_string is not None:
        for line in peers_string.split(","):
            peers = line.strip().split()

            peer_ip = None
            while peer_ip is None:
                try:
                    peer_ip = socket.gethostbyname(peers[0])
                except socket.error:
                    print "Caught socket error while resolving name! Retrying..."
                    time.sleep(0.1)
                    peer_ip = None

            peer_port = int(peers[1])
            peer_idx = int(peers[2])
            nodes[peer_idx] = (peer_ip, peer_port)

    return nodes


# Parse the ip and port based on our args/file configs.
def parse_addr(opts, params):
    ip = opts.network_ip or params['my_ip']
    assert ip is not None, "Your IP address is not specified in config.cfg or as --network-ip. Check that the '-n' " \
                           "argument reflects the name of a section in config.cfg!"

    port = int(opts.port or params['my_port'])

    return ip, port


# Configure the global logger.
def init_logging(ip, port, opts, params):
    utils.log_setmyname("%s:%d" % (ip, port))
    log_path = opts.log_path or params['log_path']
    use_stdout = opts.to_stdout or params['log_stdout']
    utils.log_init(log_path, use_stdout)
    utils.log_debug("My own IP for config purposes is {0}".format(ip))


# Creates a common parser for gateway and relay.
def get_default_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config-name",
                        help="Name of section to read from config.cfg. By default will read a section using this node's"
                             " local ip. Not needed if you specify the other options.")
    parser.add_argument("-n", "--network-ip", help="Network ip of this node")
    parser.add_argument("-p", "--peers", help="Peering string to override peers of config.cfg")
    parser.add_argument("-P", "--port", help="What port to listen on")
    parser.add_argument("-l", "--log-path", help="Path to store logfiles in")
    parser.add_argument("-o", "--to-stdout", help="Log to stdout. Doesn't generate logfiles in this mode")

    return parser

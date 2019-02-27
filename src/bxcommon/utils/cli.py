import json
import os
import re
import sys

import argparse

from bxcommon import constants
from bxcommon.connections.node_type import NodeType
from bxcommon.constants import ALL_NETWORK_NUM
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.services import sdn_http_service
from bxcommon.utils import config
from bxcommon.utils import convert, logger
from bxcommon.utils.log_level import LogLevel

# Keep here instead of constants to avoid circular import.

MANIFEST_PATH = "MANIFEST.MF"
MANIFEST_SOURCE_VERSION = "source_version"
PROTOCOL_VERSION = "protocol_version"
REQUIRED_PARAMS_IN_MANIFEST = [MANIFEST_SOURCE_VERSION]
VERSION_TYPE_LIST = ["dev", "v", "ci"]

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument("--external-ip", help="External network ip of this node", required=True)
arg_parser.add_argument("--external-port", help="External network port to listen on", type=int, required=True)
arg_parser.add_argument("--hostname", help="Hostname the node is running on", type=str, default=constants.HOSTNAME)
arg_parser.add_argument("--sdn-url", help="IP or dns of the bloxroute SDN", default=constants.SDN_ROOT_URL, type=str)
arg_parser.add_argument("--log-path", help="Path to store logfiles in")
arg_parser.add_argument("--to-stdout", help="Log to stdout. Doesn't generate logfiles in this mode",
                        type=convert.str_to_bool, default=True)
arg_parser.add_argument("--node-id", help="(TEST ONLY) Set the node_id for using in testing.")
arg_parser.add_argument("--log-level", help="set log level", type=LogLevel.__getattr__, choices=list(LogLevel))
arg_parser.add_argument("--log-flush-immediately", help="Enables immediate flush for logs",
                        type=convert.str_to_bool, default=False)

_args = None


def is_valid_version(full_version):
    """
    check if version number in template: {int}.{int}.{int}.{int} and version type is dev/ci/v
    :param full_version: {version_type}{version_number}
    :return:
    """
    try:
        version_number = full_version[re.search("\d", full_version).start():]
        version_type = full_version[:re.search("\d", full_version).start()]
        return (version_number.count(".") == 3 and all(str(x).isdigit() for x in version_number.split("."))) and \
               (version_type in VERSION_TYPE_LIST)
    except Exception:
        raise


def read_manifest(manifest_path):
    """
    read manifest file, if value invalid raise ValueError
    :param manifest_path:
    :return:
    """
    try:
        with open(manifest_path, "r") as json_file:
            json_data = json.load(json_file)
            version = json_data[MANIFEST_SOURCE_VERSION]
            try:
                if not is_valid_version(version):
                    raise ValueError("Invalid version number: {}".format(version))
                else:
                    return json_data
            except Exception:
                raise ValueError("Invalid version number: {}".format(version))

    except Exception as ex:
        raise Exception("ERROR: {}".format(str(ex)))


def get_manifest_path():
    if os.path.dirname(sys.argv[0]) == "":
        manifest_path = MANIFEST_PATH
    else:
        manifest_path = os.path.dirname(sys.argv[0]) + "/" + MANIFEST_PATH

    return manifest_path


def append_manifest_args(dict_args):
    #   set config file path
    manifest_path = get_manifest_path()
    manifest_data = read_manifest(manifest_path)
    #   if all required params exist in manifest file, update dict_args
    if all(params in manifest_data for params in REQUIRED_PARAMS_IN_MANIFEST):
        dict_args.update(manifest_data)
        dict_args.update({PROTOCOL_VERSION: bloxroute_version_manager.CURRENT_PROTOCOL_VERSION})
    else:
        missing_params = [item for item in REQUIRED_PARAMS_IN_MANIFEST if item not in manifest_data]
        raise ValueError("Missing required settings in manifest file: {}".format(", ".join(missing_params)))


def get_args():
    global _args

    if not _args:
        _args, unknown = arg_parser.parse_known_args()
        _args.external_ip = config.blocking_resolve_ip(_args.external_ip)
    return _args


def set_sdn_url():
    """
    Wraps the sdn url getter for constants to work without the CLI (e.g. in test).
    :return: URL of the SDN
    """
    constants.SDN_ROOT_URL = get_args().sdn_url
    return get_args().sdn_url


def parse_blockchain_opts(opts, node_type):
    """
    Get the blockchain network info from the SDN and set the default values for the blockchain cli params if they were
    not passed in the args.

    :param opts: argument list
    :param node_type:
    """
    opts_dict = opts.__dict__

    if node_type == NodeType.RELAY:
        opts_dict["blockchain_network_num"] = ALL_NETWORK_NUM
        return

    network_info = _get_blockchain_network_info(opts)

    for key, value in opts_dict.iteritems():
        if value is None:
            if key in network_info.default_attributes:
                opts_dict[key] = network_info.default_attributes[key.encode(constants.DEFAULT_TEXT_ENCODING)]

    opts_dict["blockchain_network_num"] = network_info.network_num
    opts_dict["blockchain_block_interval"] = network_info.block_interval
    opts_dict["blockchain_ignore_block_interval_count"] = network_info.ignore_block_interval_count


def set_blockchain_networks_info(opts):
    opts.blockchain_networks = sdn_http_service.fetch_blockchain_networks()


def _get_blockchain_network_info(opts):
    """
    Retrieves the blockchain network info from the SDN based on blockchain-protocol and blockchain-network cli arguments.

    :param opts: argument list
    """

    for blockchain_network in opts.blockchain_networks:
        if blockchain_network.protocol == opts.blockchain_protocol and blockchain_network.network == opts.blockchain_network:
            return blockchain_network

    all_networks_names = "\n".join(
        map(lambda n: "{} - {}".format(n.protocol, n.network), opts.blockchain_networks))
    error_msg = "Network number does not exist for blockchain protocol {} and network {}.\nValid options:\n{}" \
        .format(opts.blockchain_protocol, opts.blockchain_network, all_networks_names)
    logger.fatal(error_msg)
    exit(1)


def set_os_version(opts):
    opts.__dict__["os_version"] = constants.OS_VERSION


def merge_args(from_args, into_args):
    for key, val in from_args.__dict__.items():
        into_args.__dict__[key] = val

    append_manifest_args(into_args.__dict__)

    return into_args

import argparse
import json
from bxcommon.utils import convert, versions
from bxcommon import constants
from bxcommon.utils.config import blocking_resolve_ip
import os
import re
import sys

# Keep here instead of constants to avoid circular import.

MANIFEST_PATH = "MANIFEST.MF"
MANIFEST_SOURCE_VERSION = "source_version"
PROTOCOL_VERSION = "protocol_version"
REQUIRED_PARAMS_IN_MANIFEST = [MANIFEST_SOURCE_VERSION]
VERSION_TYPE_LIST = ["dev", "v", "ci"]

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument("--external-ip", help="External network ip of this node", required=True)
arg_parser.add_argument("--external-port", help="External network port to listen on", type=int, required=True)
arg_parser.add_argument("--sdn-url", help="IP or dns of the bloxroute SDN", default=constants.BX_API_ROOT_URL, type=str)
arg_parser.add_argument("--log-path", help="Path to store logfiles in")
arg_parser.add_argument("--to-stdout", help="Log to stdout. Doesn't generate logfiles in this mode",
                        type=convert.str_to_bool, default=True)
arg_parser.add_argument("--node-id", help="(TEST ONLY) Set the node_id for using in testing.")

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
        return (version_number.count(".") == 3 and all(str(x).isdigit() for x in version_number.split("."))) and\
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
        dict_args.update({PROTOCOL_VERSION: versions.get_protocol_version()})
    else:
        missing_params = [item for item in REQUIRED_PARAMS_IN_MANIFEST if item not in manifest_data]
        raise ValueError("Missing required settings in manifest file: {}".format(", ".join(missing_params)))


def get_args():
    global _args

    if not _args:
        _args, unknown = arg_parser.parse_known_args()
        _args.external_ip = blocking_resolve_ip(_args.external_ip)
    return _args


def set_sdn_url():
    """
    Wraps the sdn url getter for constants to work without the CLI (e.g. in test).
    :return: URL of the SDN
    """
    constants.BX_API_ROOT_URL = get_args().sdn_url
    return get_args().sdn_url


def merge_args(from_args, into_args):

    for key, val in from_args.__dict__.items():
        into_args.__dict__[key] = val

    append_manifest_args(into_args.__dict__)

    return into_args

import argparse

from bxcommon.utils import convert

# Keep here instead of constants to avoid circular import.
DEFAULT_BX_API_ROOT_URL = "http://127.0.0.1:8080"

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument("--source-version", help="Current node source version number in the format MAJOR.MINOR.PATCH",
                        type=str, required=True)
arg_parser.add_argument("--external-ip", help="External network ip of this node", required=True)
arg_parser.add_argument("--external-port", help="External network port to listen on", type=int, required=True)
arg_parser.add_argument("--sdn-url", help="IP or dns of the bloxroute SDN", default=DEFAULT_BX_API_ROOT_URL, type=str)
arg_parser.add_argument("--log-path", help="Path to store logfiles in")
arg_parser.add_argument("--bloxroute-version", help="Bloxroute protocol version")
arg_parser.add_argument("--to-stdout", help="Log to stdout. Doesn't generate logfiles in this mode",
                        type=convert.str_to_bool, default=True)
arg_parser.add_argument("--node-id", help="(TEST ONLY) Set the node_id for using in testing.")

_args = None


def get_args():
    global _args

    if not _args:
        _args, unknown = arg_parser.parse_known_args()

    return _args


def get_sdn_url():
    """
    Wraps the sdn url getter for constants to work without the CLI (e.g. in test).
    :return: URL of the SDN
    """
    try:
        return get_args().sdn_url
    except BaseException:
        return DEFAULT_BX_API_ROOT_URL


def merge_args(from_args, into_args):
    for key, val in from_args.__dict__.items():
        into_args.__dict__[key] = val

    return into_args

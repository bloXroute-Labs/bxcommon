import argparse

from bxcommon.utils import convert

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument("--node-id", help="Set the node_id for using in testing.")
arg_parser.add_argument("--external-ip", help="External network ip of this node")
arg_parser.add_argument("--external-port", help="External network port to listen on", type=int)
arg_parser.add_argument("--internal-ip", help="IP of the system nic")
arg_parser.add_argument("--internal-port", help="Port of the system nic", type=int)
arg_parser.add_argument("--log-path", help="Path to store logfiles in")
arg_parser.add_argument("--sdn-url", help="IP or dns of the bloxroute SDN", default="http://127.0.0.1:8080", type=str)
arg_parser.add_argument("--sdn-socket-ip", help="Socket connection ip for SDN", type=str)
arg_parser.add_argument("--sdn-socket-port", help="Socket connection port for SDN", type=int)
arg_parser.add_argument("--bloxroute-version", help="Bloxroute protocol version")
arg_parser.add_argument("--to-stdout", help="Log to stdout. Doesn't generate logfiles in this mode",
                        type=convert.str_to_bool, default=True)

_args = None

def get_args():
    global _args

    if not _args:
        _args, unknown = arg_parser.parse_known_args()

    return _args


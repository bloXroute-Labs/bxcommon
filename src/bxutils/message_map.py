from bxutils import log_messages
from typing import Dict, Any, List

logger_names = set("bxcommon")

message_map = {
    log_messages.EMPTY_BLOCKCHAIN_NETWORK_LIST: ("Empty list for blockchain networks "
                                                 "from SDN, trying to obtain info from cache"),
    log_messages.READ_CACHE_FILE_ERROR: "Failed when tried to read from cache file: could not find the specified file"
}


def update_log_messages(node_message: Dict[Any, Any], node_logger_names: List):
    message_map.update(node_message)
    logger_names.update(node_logger_names)


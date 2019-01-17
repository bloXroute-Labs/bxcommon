from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.hello_message import HelloMessage


def hello_message():
    return HelloMessage(protocol_version=bloxroute_version_manager.CURRENT_PROTOCOL_VERSION,
                        network_num=DEFAULT_NETWORK_NUM)

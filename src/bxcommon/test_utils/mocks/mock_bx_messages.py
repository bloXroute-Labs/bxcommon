from bxcommon.constants import DEFAULT_NETWORK_NUM
from bxcommon.messages.bloxroute.bloxroute_version_manager import bloxroute_version_manager
from bxcommon.messages.bloxroute.hello_message import HelloMessage


def hello_message():
    return HelloMessage(bloxroute_version_manager.CURRENT_PROTOCOL_VERSION, DEFAULT_NETWORK_NUM, 1)
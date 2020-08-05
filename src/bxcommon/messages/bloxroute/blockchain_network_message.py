from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging import LogLevel


class RefreshBlockchainNetworkMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.REFRESH_BLOCKCHAIN_NETWORK
    """
    Request sdn to refresh blockchain network model
    """

    def __init__(self, buf: Optional[bytearray] = None) -> None:
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + constants.CONTROL_FLAGS_LEN)
            self.buf = buf

        super(RefreshBlockchainNetworkMessage, self).__init__(self.MESSAGE_TYPE, constants.CONTROL_FLAGS_LEN, buf)

    def log_level(self):
        return LogLevel.DEBUG

    def __repr__(self):
        return "RefreshBlockchainNetworkMessage<>"

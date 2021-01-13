from typing import Dict, Any
from bxcommon import constants
from bxcommon.messages.abstract_internal_message import AbstractInternalMessage
from bxcommon.messages.bloxroute.bloxroute_message_control_flags import BloxrouteMessageControlFlags
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType


class AbstractBloxrouteMessage(AbstractInternalMessage):
    """
    Base class for internal communication between relays and gateways
    """

    MESSAGE_TYPE = BloxrouteMessageType.ABSTRACT_INTERNAL
    HEADER_LENGTH = constants.STARTING_SEQUENCE_BYTES_LEN + constants.BX_HDR_COMMON_OFF
    STARTING_BYTES_LEN = constants.STARTING_SEQUENCE_BYTES_LEN

    converted_message: Dict[int, Any]

    def __init__(self, msg_type: bytes, payload_len: int, buf: bytearray) -> None:

        super().__init__(msg_type=msg_type, payload_len=payload_len, buf=buf)

        buf[:constants.STARTING_SEQUENCE_BYTES_LEN] = constants.STARTING_SEQUENCE_BYTES

        # Control flag is set to TRUE by default
        self.set_control_flag(BloxrouteMessageControlFlags.VALID)
        self.converted_message = {}

    def get_control_flags(self) -> int:
        """
        Returns byte containing control flags for the message
        :return: byte with control flags
        """
        return self._memoryview[-1]

    def set_control_flag(self, flag: int) -> None:
        """
        Sets value to control flag
        :param flag: control flag to set
        """
        self.buf[-1] |= flag

    def remove_control_flag(self, flag: int) -> None:
        """
        Removes control flag value
        :param flag: flag value to remove
        """
        if self.buf[-1] & flag:
            self.buf[-1] ^= flag

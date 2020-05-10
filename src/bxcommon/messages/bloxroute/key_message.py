from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxutils.logging.log_level import LogLevel


class KeyMessage(AbstractBroadcastMessage):
    MESSAGE_TYPE = BloxrouteMessageType.KEY
    PAYLOAD_LENGTH = AbstractBroadcastMessage.PAYLOAD_LENGTH + crypto.KEY_SIZE

    def __init__(self, message_hash: Optional[Sha256Hash] = None, network_num: Optional[int] = None,
                 source_id: str = "", key: Optional[bytearray] = None, buf: Optional[bytearray] = None):
        self._key = None
        self._block_id = None

        super().__init__(message_hash, network_num, source_id, buf)

        if buf is None:
            # pyre-fixme[6]: Expected `Sized` for 1st param but got
            #  `Optional[bytearray]`.
            if len(key) != crypto.KEY_SIZE:
                raise ValueError(f"Key must be of size {crypto.KEY_SIZE}")

            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN
            self.buf[off:off + crypto.KEY_SIZE] = key

    def log_level(self):
        return LogLevel.DEBUG

    def block_hash(self) -> Sha256Hash:
        return self.message_hash()

    def key(self) -> memoryview:
        if self._key is None:
            off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN
            self._key = self._memoryview[off:off + crypto.KEY_SIZE]

        # pyre-fixme[7]: Expected `memoryview` but got `None`.
        return self._key

    def __repr__(self):
        return f"KeyMessage<network_num: {self.network_num()}, block_id: {self.message_id()}"

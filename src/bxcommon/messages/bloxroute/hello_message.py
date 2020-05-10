from typing import Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.protocol_version import PROTOCOL_VERSION
from bxcommon.messages.bloxroute.version_message import VersionMessage
from bxcommon.utils import uuid_pack
from bxcommon.utils.message_buffer_builder import PayloadElement, PayloadBlock


class HelloMessage(VersionMessage):
    """
    BloXroute relay hello message type.

    node_id: the id of the node

    """
    MESSAGE_TYPE = BloxrouteMessageType.HELLO
    HELLO_MESSAGE_BLOCK = PayloadBlock(
        VersionMessage.BASE_LENGTH,
        "HelloMessage",
        PROTOCOL_VERSION,
        PayloadElement(
            name="node_id",
            structure="%ss" % constants.NODE_ID_SIZE_IN_BYTES,
            encode=uuid_pack.to_bytes,
            decode=uuid_pack.from_bytes
        )
    )
    HELLO_MESSAGE_LENGTH = (
        VersionMessage.VERSION_MESSAGE_BLOCK.size
        + HELLO_MESSAGE_BLOCK.size
        + constants.CONTROL_FLAGS_LEN
    )

    # pyre-fixme[9]: node_id has type `str`; used as `None`.
    def __init__(self, protocol_version: Optional[int] = None, network_num: Optional[int] = None, node_id: str = None,
                 # pyre-fixme[9]: buf has type `bytearray`; used as `None`.
                 buf: bytearray = None):
        if buf is None:
            buf = bytearray(self.HEADER_LENGTH + self.HELLO_MESSAGE_LENGTH)
            buf = self.HELLO_MESSAGE_BLOCK.build(buf, node_id=node_id)

        self.buf = buf
        self._node_id = None
        self._network_num = None
        self._memoryview = memoryview(buf)
        super(HelloMessage, self).__init__(self.MESSAGE_TYPE, self.HELLO_MESSAGE_LENGTH,
                                           protocol_version, network_num, buf)

    def __unpack(self):
        contents = self.HELLO_MESSAGE_BLOCK.read(self._memoryview)
        self._node_id = contents.get("node_id")

    def node_id(self):
        if self._node_id is None:
            self.__unpack()
        return self._node_id

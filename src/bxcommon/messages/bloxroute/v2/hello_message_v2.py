import struct

from bxcommon.constants import UL_INT_SIZE_IN_BYTES, NETWORK_NUM_LEN, VERSION_NUM_LEN, HDR_COMMON_OFF
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.version_message import VersionMessage

_IDX_LEN = UL_INT_SIZE_IN_BYTES


class HelloMessageV2(VersionMessage):
    """
    BloXroute relay hello message type.

    idx: index of the peer.
        Client will use 0 and will not be connected back to
        Other bloXroute servers send a positive identity specified in config file
    """
    MESSAGE_TYPE = BloxrouteMessageType.HELLO
    HelloMessageLength = VersionMessage.VERSION_MESSAGE_LENGTH + _IDX_LEN

    def __init__(self, protocol_version=None, network_num=None, idx=None, buf=None):

        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + self.HelloMessageLength)
            off = VersionMessage.BASE_LENGTH
            struct.pack_into("<L", buf, off, idx)

        self.buf = buf
        self._idx = None
        self._network_num = None
        self._memoryview = memoryview(buf)

        super(HelloMessageV2, self).__init__(self.MESSAGE_TYPE, self.HelloMessageLength,
                                             protocol_version, network_num, buf)

    def idx(self):
        if self._idx is None:
            off = VersionMessage.BASE_LENGTH
            self._idx, = struct.unpack_from("<L", self.buf, off)
        return self._idx

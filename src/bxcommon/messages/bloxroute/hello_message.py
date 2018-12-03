import struct

from bxcommon.constants import HDR_COMMON_OFF, UL_INT_SIZE_IN_BYTES, NETWORK_NUM_LEN, VERSION_NUM_LEN
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message

_IDX_LEN = UL_INT_SIZE_IN_BYTES

class HelloMessage(Message):
    """
    BloXroute relay hello message type.

    idx: index of the peer.
        Client will use 0 and will not be connected back to
        Other bloXroute servers send a positive identity specified in config file
    """
    MESSAGE_TYPE = BloxrouteMessageType.HELLO

    def __init__(self, protocol_version=None, idx=None, network_num=None, buf=None):

        if buf is None:
            buf = bytearray(HDR_COMMON_OFF + VERSION_NUM_LEN + _IDX_LEN + NETWORK_NUM_LEN)
            self.buf = buf
            off = HDR_COMMON_OFF
            struct.pack_into("<L", buf, off, protocol_version)
            off += VERSION_NUM_LEN
            struct.pack_into("<L", buf, off, idx)
            off += _IDX_LEN
            struct.pack_into("<L", buf, off, network_num)

            super(HelloMessage, self).__init__(self.MESSAGE_TYPE, VERSION_NUM_LEN + _IDX_LEN + NETWORK_NUM_LEN, buf)
        else:
            self.buf = buf
            self._msg_type = self._payload_len = self._payload = None

        self._protocol_version = None
        self._idx = None
        self._network_num = None
        self._memoryview = memoryview(buf)

    def protocol_version(self):
        if self._protocol_version is None:
            off = HDR_COMMON_OFF
            self._protocol_version, = struct.unpack_from("<L", self.buf, off)
        return self._protocol_version

    def idx(self):
        if self._idx is None:
            off = HDR_COMMON_OFF + VERSION_NUM_LEN
            self._idx, = struct.unpack_from("<L", self.buf, off)
        return self._idx

    def network_num(self):
        if self._network_num is None:
            off = HDR_COMMON_OFF + VERSION_NUM_LEN + _IDX_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)
        return self._network_num

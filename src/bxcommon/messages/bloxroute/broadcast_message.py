import struct

from bxcommon.constants import HDR_COMMON_OFF, NETWORK_NUM_LEN
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.message import Message
from bxcommon.utils.buffers.input_buffer import InputBuffer
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import ObjectHash


class BroadcastMessage(Message):
    MESSAGE_TYPE = BloxrouteMessageType.BROADCAST

    def __init__(self, msg_hash=None, network_num=None, blob=None, buf=None):
        if buf is None:
            self.buf = bytearray(HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN + len(blob))

            off = HDR_COMMON_OFF
            self.buf[off:off + SHA256_HASH_LEN] = msg_hash.binary
            off += SHA256_HASH_LEN
            struct.pack_into("<L", self.buf, off, network_num)
            off += NETWORK_NUM_LEN
            self.buf[off:off + len(blob)] = blob
            off += len(blob)

            super(BroadcastMessage, self).__init__(self.MESSAGE_TYPE, off - HDR_COMMON_OFF, self.buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

        self._msg_hash = None
        self._network_num = None
        self._blob = None

    def msg_hash(self):
        if self._msg_hash is None:
            off = HDR_COMMON_OFF
            self._msg_hash = ObjectHash(self._memoryview[off:off + SHA256_HASH_LEN])
        return self._msg_hash

    def network_num(self):
        if self._network_num is None:
            off = HDR_COMMON_OFF + SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)

        return self._network_num

    def blob(self):
        if self._blob is None:
            off = HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN
            self._blob = self._memoryview[off:off + self.payload_len()]

        return self._blob
    
    @classmethod
    def peek_network_num(cls, input_buffer):
        if not isinstance(input_buffer, InputBuffer):
            raise TypeError("Arg input_buffer expected type in InputBuffer but was {}".format(type(input_buffer)))

        off = HDR_COMMON_OFF + SHA256_HASH_LEN

        if input_buffer.length < off + NETWORK_NUM_LEN:
            raise ValueError("Not enough bytes to peek network number.")

        network_num_bytes = input_buffer.peek_message(off + NETWORK_NUM_LEN)

        network_num, = struct.unpack_from("<L", network_num_bytes, off)

        return network_num



import struct

from bxcommon import constants
from bxcommon.constants import BX_HDR_COMMON_OFF, NETWORK_NUM_LEN
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.v4.message_v4 import MessageV4
from bxcommon.utils.crypto import SHA256_HASH_LEN
from bxcommon.utils.object_hash import Sha256Hash


class TxMessageV4(MessageV4):
    MESSAGE_TYPE = BloxrouteMessageType.TRANSACTION
    EMPTY_TX_VAL = memoryview(bytes())

    def __init__(self, tx_hash=None, network_num=None, sid=constants.NULL_TX_SID, tx_val=None, buf=None):
        self._tx_hash = None
        self._short_id = None
        self._network_num = None
        self._tx_val = None
        self._payload_len = None
        self._payload = None

        if buf is None:
            if tx_val is None:
                tx_val = bytes()

            buf = bytearray(BX_HDR_COMMON_OFF + SHA256_HASH_LEN + constants.SID_LEN + NETWORK_NUM_LEN)
            self.buf = buf

            off = BX_HDR_COMMON_OFF
            self.buf[off:off + SHA256_HASH_LEN] = tx_hash.binary
            off += SHA256_HASH_LEN
            struct.pack_into("<L", buf, off, network_num)
            off += NETWORK_NUM_LEN
            struct.pack_into("<L", buf, off, sid)
            off += constants.SID_LEN
            self.buf[off:off + len(tx_val)] = tx_val
            off += len(tx_val)

            super(TxMessageV4, self).__init__(self.MESSAGE_TYPE, off - BX_HDR_COMMON_OFF, buf)
        else:
            assert not isinstance(buf, str)
            self.buf = buf
            self._memoryview = memoryview(self.buf)

    def tx_hash(self):
        if self._tx_hash is None:
            off = BX_HDR_COMMON_OFF
            self._tx_hash = Sha256Hash(self._memoryview[off:off + SHA256_HASH_LEN])
        return self._tx_hash

    def network_num(self):
        if self._network_num is None:
            off = BX_HDR_COMMON_OFF + SHA256_HASH_LEN
            self._network_num, = struct.unpack_from("<L", self.buf, off)

        return self._network_num

    def short_id(self):
        if self._short_id is None:
            off = BX_HDR_COMMON_OFF + SHA256_HASH_LEN + NETWORK_NUM_LEN
            self._short_id, = struct.unpack_from("<L", self.buf[off:off + constants.SID_LEN], 0)

        if self._short_id != constants.NULL_TX_SID:
            return self._short_id

    def tx_val(self):
        if self._tx_val is None:
            if self.payload_len() == 0:
                self._tx_val = self.EMPTY_TX_VAL
            else:
                off = BX_HDR_COMMON_OFF + SHA256_HASH_LEN + constants.SID_LEN + NETWORK_NUM_LEN
                self._tx_val = self._memoryview[off:off + self.payload_len()]

        return self._tx_val

    def __repr__(self):
        return ("TxMessage<tx_hash: {}, short_id: {}, network_num: {}, compact:{}>"
                .format(self.tx_hash(), self.short_id(), self.network_num(), self.tx_val() == self.EMPTY_TX_VAL))

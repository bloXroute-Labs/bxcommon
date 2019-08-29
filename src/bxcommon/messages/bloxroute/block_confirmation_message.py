import struct
from typing import List, Optional, Iterable

from bxcommon.utils import crypto
from bxcommon import constants
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.utils.object_hash import Sha256Hash
from bxcommon.utils.log_level import LogLevel


class BlockConfirmationMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.BLOCK_CONFIRMATION
    """
    Message with sids numbers for cleanup.
    """

    def __init__(self,
                 sids: Optional[List[int]] = None,
                 tx_hashes: Optional[List[Sha256Hash]] = None,
                 buf: Optional[bytearray] = None,
                 block_hash: Optional[Sha256Hash] = None,
                 network_num: Optional[int] = None
                 ):

        """
        Constructor. Expects list of transaction sids

        :param sids: list of sids
        :param buf: message bytes
        """

        if buf is None:
            buf = self._payload_to_bytes(network_num, block_hash, sids, tx_hashes)
            super(BlockConfirmationMessage, self).__init__(self.MESSAGE_TYPE, len(buf) - self.HEADER_LENGTH, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

        self._network_num = None
        self._tx_hashes = None
        self._sids = None
        self._block_hash = None
        self._sids_count = None
        self._hashes_count = None

    def log_level(self):
        return LogLevel.INFO

    def get_sids(self) -> List[int]:
        if self._sids is None:
            self._parse()

        assert self._sids is not None
        return self._sids

    def get_block_hash(self) -> Sha256Hash:
        if self._block_hash is None:
            self._parse_header()
        assert self._block_hash is not None
        return self._block_hash

    def get_tx_hashes(self) -> List[Sha256Hash]:
        if self._tx_hashes is None:
            self._parse()
        assert self._tx_hashes is not None
        return self._tx_hashes

    def network_num(self) -> int:
        if self._network_num is None:
            self._parse_header()
        assert self._network_num is not None
        return self._network_num

    def _payload_to_bytes(self, network_num: int, block_hash: Sha256Hash, sids: List[int], tx_hashes: List[Sha256Hash]):

        sid_count = len(sids)
        hashes_count = len(tx_hashes)

        # msg_size = HDR_COMMON_OFF + sid tx count + (sid ) of each tx + tx hash count + ( hash ) of each tx
        msg_size = self.HEADER_LENGTH + \
            constants.UL_INT_SIZE_IN_BYTES + \
            crypto.SHA256_HASH_LEN + \
            constants.UL_INT_SIZE_IN_BYTES +\
            sid_count * constants.UL_INT_SIZE_IN_BYTES + \
            constants.UL_INT_SIZE_IN_BYTES + \
            hashes_count * crypto.SHA256_HASH_LEN + \
            constants.CONTROL_FLAGS_LEN

        buf = bytearray(msg_size)
        off = self.HEADER_LENGTH

        struct.pack_into("<L", buf, off, network_num)
        off += constants.NETWORK_NUM_LEN

        buf[off:off + crypto.SHA256_HASH_LEN] = block_hash
        off += crypto.SHA256_HASH_LEN

        struct.pack_into("<L", buf, off, sid_count)
        off += constants.UL_INT_SIZE_IN_BYTES

        for sid in sids:
            struct.pack_into("<L", buf, off, sid)
            off += constants.UL_INT_SIZE_IN_BYTES

        struct.pack_into("<L", buf, off, hashes_count)
        off += constants.UL_INT_SIZE_IN_BYTES

        for tx_hash in tx_hashes:
            buf[off:off + crypto.SHA256_HASH_LEN] = tx_hash
            off += crypto.SHA256_HASH_LEN

        return buf

    def _parse_header(self):
        off = self.HEADER_LENGTH
        self._network_num, = struct.unpack_from("<L", self._memoryview, off)
        off += constants.NETWORK_NUM_LEN
        self._block_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])
        off += crypto.SHA256_HASH_LEN
        self._sids_count, = struct.unpack_from("<L", self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES + (self._sids_count * constants.UL_INT_SIZE_IN_BYTES)
        self._hashes_count, = struct.unpack_from("<L", self.buf, off)

    def _parse(self):
        sids = []
        tx_hashes = []
        if self._sids_count is None:
            self._parse_header()

        off = self.HEADER_LENGTH + constants.NETWORK_NUM_LEN + crypto.SHA256_HASH_LEN + constants.UL_INT_SIZE_IN_BYTES
        for sid_index in range(self._sids_count):
            sid, = struct.unpack_from("<L", self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            sids.append(sid)

        off += constants.UL_INT_SIZE_IN_BYTES

        for tx_hash in range(self._hashes_count):
            tx_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])
            off += crypto.SHA256_HASH_LEN

            tx_hashes.append(tx_hash)

        self._sids = sids
        self._tx_hashes = tx_hashes

    def __repr__(self):
        return "BlockConfirmationMessage <block_hash: {} :{}> <num_sids: {}> <num_tx_hashes: {}>".format(
            self.get_block_hash(),
            self._network_num,
            self._sids_count,
            self._hashes_count
        )

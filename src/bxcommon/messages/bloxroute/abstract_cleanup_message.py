import struct
from typing import List, Optional

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxutils.logging.log_level import LogLevel


class AbstractCleanupMessage(AbstractBroadcastMessage):
    PAYLOAD_START_OFFSET = AbstractBroadcastMessage.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - \
        constants.CONTROL_FLAGS_LEN

    """
    Message with sids numbers for cleanup.
    """

    _tx_hashes: Optional[List[Sha256Hash]] = None
    _sids: Optional[List[int]] = None
    _sids_count: Optional[int] = None
    _tx_hashes_count: Optional[int] = None

    def __init__(
        self,
        message_hash: Optional[Sha256Hash] = None,
        network_num: Optional[int] = None,
        source_id: str = "",
        sids: Optional[List[int]] = None,
        tx_hashes: Optional[List[Sha256Hash]] = None,
        buf: Optional[bytearray] = None
    ) -> None:

        if buf is None:
            assert tx_hashes is not None and sids is not None
            # pylint: disable=invalid-name
            self.PAYLOAD_LENGTH = (
                AbstractBroadcastMessage.PAYLOAD_LENGTH
                + (constants.UL_INT_SIZE_IN_BYTES * 2)
                + (len(sids) * constants.UL_INT_SIZE_IN_BYTES)
                + (len(tx_hashes) * crypto.SHA256_HASH_LEN)
            )

        super(AbstractCleanupMessage, self).__init__(message_hash, network_num, source_id, buf)

        if buf is None:
            assert tx_hashes is not None and sids is not None
            sid_count = len(sids)
            hashes_count = len(tx_hashes)
            off = self.PAYLOAD_START_OFFSET

            struct.pack_into("<L", self.buf, off, sid_count)
            off += constants.UL_INT_SIZE_IN_BYTES

            for sid in sids:
                struct.pack_into("<L", self.buf, off, sid)
                off += constants.UL_INT_SIZE_IN_BYTES

            struct.pack_into("<L", self.buf, off, hashes_count)
            off += constants.UL_INT_SIZE_IN_BYTES

            for tx_hash in tx_hashes:
                self.buf[off:off + crypto.SHA256_HASH_LEN] = tx_hash
                off += crypto.SHA256_HASH_LEN

    def log_level(self) -> LogLevel:
        return LogLevel.DEBUG

    def short_ids(self) -> List[int]:
        if self._sids is None:
            self._parse()

        sids = self._sids
        assert sids is not None
        return sids

    def transaction_hashes(self) -> List[Sha256Hash]:
        if self._tx_hashes is None:
            self._parse()

        tx_hashes = self._tx_hashes
        assert tx_hashes is not None
        return tx_hashes

    def _parse(self) -> None:
        off = self.HEADER_LENGTH + AbstractBroadcastMessage.PAYLOAD_LENGTH - constants.CONTROL_FLAGS_LEN

        sids = []
        sids_count, = struct.unpack_from("<L", self.buf, off)
        self._sids_count = sids_count
        off += constants.UL_INT_SIZE_IN_BYTES

        for _ in range(sids_count):
            sid, = struct.unpack_from("<L", self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            sids.append(sid)

        tx_hashes = []
        tx_hashes_count, = struct.unpack_from("<L", self.buf, off)
        self._tx_hashes_count = tx_hashes_count
        off += constants.UL_INT_SIZE_IN_BYTES

        for tx_hash in range(tx_hashes_count):
            tx_hash = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])
            off += crypto.SHA256_HASH_LEN

            tx_hashes.append(tx_hash)

        self._sids = sids
        self._tx_hashes = tx_hashes

    def __repr__(self) -> str:
        return "{} <message: {} :{}> <num_sids: {}> <num_tx_hashes: {}>".format(
            self.MESSAGE_TYPE.name,
            self.message_hash(),
            self._network_num,
            self._sids_count,
            self._tx_hashes_count
        )

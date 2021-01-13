import struct
from typing import List, Optional

from bxcommon import constants
from bxcommon.messages.bloxroute import transactions_info_serializer
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.messages.bloxroute.txs_message import TxsMessage
from bxcommon.models.transaction_info import TransactionInfo
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash
from bxutils import logging

logger = logging.get_logger(__name__)


class CompressedBlockTxsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.COMPRESSED_BLOCK_TXS
    """
    Message with tx details. Reply to GetTxsMessage.
    """

    _txs: Optional[List[TransactionInfo]] = None
    _network_num: Optional[int] = None
    _block_hash: Optional[Sha256Hash] = None

    def __init__(
        self,
        network_num: Optional[int] = None,
        block_hash: Optional[Sha256Hash] = None,
        txs: Optional[List[TransactionInfo]] = None,
        buf: Optional[bytearray] = None
    ) -> None:

        """
        Constructor. Expects list of transaction details or message bytes.
        :param network_num: Network number
        :param block_hash: Block hash
        :param txs: tuple with 3 values (tx short id, tx hash, tx contents)
        :param buf: message bytes
        """
        self.txs_info_offset = self.HEADER_LENGTH + constants.UL_INT_SIZE_IN_BYTES + crypto.SHA256_HASH_LEN

        if buf is None:
            assert network_num is not None
            assert block_hash is not None
            assert txs is not None
            buf = self._serialize(network_num, block_hash, txs)
        super().__init__(self.MESSAGE_TYPE, len(buf) - self.HEADER_LENGTH, buf)

        self._txs = None
        self._txs_count = None
        self._network_num = None
        self._block_hash = None

    def get_txs(self) -> List[TransactionInfo]:
        if self._txs is None:
            self._parse()

        txs = self._txs
        assert txs is not None
        return txs

    def get_txs_count(self) -> Optional[int]:
        if self._txs_count is None:
            off = self.HEADER_LENGTH + constants.UL_INT_SIZE_IN_BYTES + crypto.SHA256_HASH_LEN
            self._txs_count, = struct.unpack_from("<L", self.buf, off)

        return self._txs_count

    def block_hash(self) -> Sha256Hash:
        if self._block_hash is None:
            self._parse()

        block_hash = self._block_hash
        assert block_hash is not None
        return block_hash

    def network_num(self) -> int:
        if self._network_num is None:
            self._parse()

        network_num = self._network_num
        assert network_num is not None
        return network_num

    def to_txs_message(self) -> TxsMessage:
        txs_info_bytes = self.rawbytes()[self.txs_info_offset:]
        result_message_bytes = bytearray(TxsMessage.HEADER_LENGTH + len(txs_info_bytes))
        result_message_bytes[TxsMessage.HEADER_LENGTH:] = txs_info_bytes
        return TxsMessage(buf=result_message_bytes)

    def _serialize(self, network_num: int, block_hash: Sha256Hash, txs_details: List[TransactionInfo]):

        msg_size = (
            self.txs_info_offset
            + transactions_info_serializer.get_serialized_length(txs_details)
            + constants.CONTROL_FLAGS_LEN
        )

        buf = bytearray(msg_size)
        off = self.HEADER_LENGTH

        struct.pack_into("<L", buf, off, network_num)
        off += constants.UL_INT_SIZE_IN_BYTES

        buf[off:off + crypto.SHA256_HASH_LEN] = block_hash.binary
        off += crypto.SHA256_HASH_LEN

        transactions_info_serializer.serialize_transactions_info_to_buffer(txs_details, buf, off)

        return buf

    def _parse(self):
        off = self.HEADER_LENGTH

        self._network_num, = struct.unpack_from("<L", self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

        self._block_hash = Sha256Hash(self.buf[off: off + crypto.SHA256_HASH_LEN])
        off += crypto.SHA256_HASH_LEN

        txs, _ = transactions_info_serializer.deserialize_transactions_info_from_buffer(self.buf, off)

        self._txs = txs

    def __repr__(self):
        return "CompressedBlockTxsMessage<num_txs: {}>".format(len(self.get_txs()))

    def __iter__(self):
        for short_id in self.get_txs():
            yield short_id

    def __len__(self):
        return len(self.get_txs())

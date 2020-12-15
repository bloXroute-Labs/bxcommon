import struct
from typing import Optional, List, Union

from bxcommon import constants
from bxcommon.messages.bloxroute import short_ids_serializer
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils import crypto
from bxcommon.utils.object_hash import Sha256Hash


class GetCompressedBlockTxsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.GET_COMPRESSED_BLOCK_TXS

    """
    Message used to request information about services with specified short ids.
    Node needs to reply with TxsWithShortIdsMessage
    """

    _network_num: Optional[int] = None
    _block_hash: Optional[Sha256Hash] = None
    _short_ids: Optional[List[int]] = None

    def __init__(
        self,
        network_num: Optional[int] = None,
        block_hash: Optional[Sha256Hash] = None,
        short_ids: Optional[List[int]] = None,
        buf: Optional[Union[bytearray, memoryview]] = None
    ) -> None:

        """
        Constructor. Expects list of short ids or message bytes.

        :param network_num Network number
        :param block_hash Block hash
        :param short_ids: list of short ids
        :param buf: message bytes
        """

        if buf is None:
            buf = self._serialize(network_num, block_hash, short_ids)
            super().__init__(self.MESSAGE_TYPE, len(buf) - self.HEADER_LENGTH, buf)
        else:
            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

        self._network_num = None
        self._block_hash = None
        self._short_ids = None

    def get_short_ids(self) -> List[int]:
        if self._short_ids is None:
            self._parse()

        short_ids = self._short_ids
        assert short_ids is not None
        return short_ids

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

    def get_serialized_short_ids(self):
        return self.rawbytes()[
               self.HEADER_LENGTH + constants.UL_INT_SIZE_IN_BYTES + crypto.SHA256_HASH_LEN:
               -constants.CONTROL_FLAGS_LEN]

    def _serialize(self, network_num, block_hash, short_ids):
        msg_size = (
            constants.STARTING_SEQUENCE_BYTES_LEN
            + constants.BX_HDR_COMMON_OFF
            + constants.UL_INT_SIZE_IN_BYTES
            + crypto.SHA256_HASH_LEN
            + short_ids_serializer.get_serialized_length(len(short_ids))
            + constants.CONTROL_FLAGS_LEN
        )

        buf = bytearray(msg_size)

        off = self.HEADER_LENGTH

        struct.pack_into("<L", buf, off, network_num)
        off += constants.UL_INT_SIZE_IN_BYTES

        buf[off:off + crypto.SHA256_HASH_LEN] = block_hash.binary
        off += crypto.SHA256_HASH_LEN

        short_ids_serializer.serialize_short_ids_to_buffer(short_ids, buf, off)

        return buf

    def _parse(self):
        off = self.HEADER_LENGTH

        self._network_num, = struct.unpack_from("<L", self.buf, off)
        off += constants.UL_INT_SIZE_IN_BYTES

        self._block_hash = Sha256Hash(self.buf[off: off + crypto.SHA256_HASH_LEN])
        off += crypto.SHA256_HASH_LEN

        short_ids, _ = short_ids_serializer.deserialize_short_ids_from_buffer(self.buf, off)

        self._short_ids = short_ids

    def __repr__(self):
        return "GetCompressedBlockTxsMessage<num_short_ids: {}>".format(len(self.get_short_ids()))

    def __iter__(self):
        for short_id in self.get_short_ids():
            yield short_id

    def __len__(self):
        return len(self.get_short_ids())

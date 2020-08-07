from bxcommon import constants
from bxcommon.messages.bloxroute import short_ids_serializer
from bxcommon.messages.bloxroute.abstract_bloxroute_message import AbstractBloxrouteMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxutils.logging.log_level import LogLevel


class GetTxsMessage(AbstractBloxrouteMessage):
    MESSAGE_TYPE = BloxrouteMessageType.GET_TRANSACTIONS

    """
    Message used to request information about services with specified short ids.
    Node needs to reply with TxsWithShortIdsMessage
    """

    def __init__(self, short_ids=None, buf=None) -> None:

        """
        Constructor. Expects list of short ids or message bytes.

        :param short_ids: list of short ids
        :param buf: message bytes
        """

        self._short_ids = None
        if buf is None:
            buf = self._short_ids_to_bytes(short_ids)
            super(GetTxsMessage, self).__init__(self.MESSAGE_TYPE, len(buf) - self.HEADER_LENGTH, buf)
        else:
            if isinstance(buf, str):
                raise TypeError("Buffer can't be string")

            self.buf = buf
            self._memoryview = memoryview(self.buf)
            self._payload_len = None
            self._payload = None

    def log_level(self):
        return LogLevel.DEBUG

    def get_short_ids(self):
        if self._short_ids is None:
            self._parse()

        return self._short_ids

    def get_serialized_short_ids(self):
        return self.rawbytes()[self.HEADER_LENGTH:-constants.CONTROL_FLAGS_LEN]

    def _short_ids_to_bytes(self, short_ids):
        msg_size = (
            constants.STARTING_SEQUENCE_BYTES_LEN
            + constants.BX_HDR_COMMON_OFF
            + short_ids_serializer.get_serialized_length(len(short_ids))
            + constants.CONTROL_FLAGS_LEN
        )

        buf = bytearray(msg_size)
        off = self.HEADER_LENGTH
        short_ids_serializer.serialize_short_ids_to_buffer(short_ids, buf, off)
        return buf

    def _parse(self):
        self._short_ids, _ = short_ids_serializer.deserialize_short_ids_from_buffer(self.buf, self.HEADER_LENGTH)

    def __repr__(self):
        return "GetTxsMessage<num_short_ids: {}>".format(len(self.get_short_ids()))

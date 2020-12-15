import struct
from typing import Optional, List, Union

from bxcommon import constants
from bxcommon.messages.bloxroute.abstract_broadcast_message import AbstractBroadcastMessage
from bxcommon.messages.bloxroute.bloxroute_message_type import BloxrouteMessageType
from bxcommon.utils import uuid_pack, crypto
from bxcommon.utils.object_hash import Sha256Hash


class RoutingUpdateMessage(AbstractBroadcastMessage):
    MESSAGE_TYPE = BloxrouteMessageType.ROUTING_UPDATE
    PAYLOAD_LENGTH = (
        AbstractBroadcastMessage.PAYLOAD_LENGTH
        + constants.NODE_ID_SIZE_IN_BYTES
        + constants.NODE_ID_SIZE_IN_BYTES
        + crypto.SHA256_HASH_LEN
        + constants.UL_INT_SIZE_IN_BYTES
    )

    _origin_node_id: Optional[str] = None
    _forwarding_node_id: Optional[str] = None
    _routing_update_id: Optional[Sha256Hash] = None
    _routing_update: Optional[List[str]] = None

    def __init__(
        self,
        message_hash: Optional[Sha256Hash] = None,
        source_id: str = "",
        origin_node_id: Optional[str] = None,
        forwarding_node_id: Optional[str] = None,
        routing_update_id: Optional[Sha256Hash] = None,
        routing_update: Optional[List[str]] = None,
        buf: Optional[Union[bytearray, memoryview]] = None
    ) -> None:

        if routing_update is not None:
            # pylint: disable=invalid-name
            self.PAYLOAD_LENGTH += len(routing_update) * constants.NODE_ID_SIZE_IN_BYTES

        super().__init__(message_hash, constants.ALL_NETWORK_NUM, source_id, buf)

        if buf is None:
            assert origin_node_id is not None
            assert routing_update is not None
            assert forwarding_node_id is not None
            assert routing_update_id is not None

            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
            )

            struct.pack_into("<16s", self.buf, off, uuid_pack.to_bytes(origin_node_id))
            off += constants.NODE_ID_SIZE_IN_BYTES

            struct.pack_into("<16s", self.buf, off, uuid_pack.to_bytes(forwarding_node_id))
            off += constants.NODE_ID_SIZE_IN_BYTES

            self.buf[off:off + crypto.SHA256_HASH_LEN] = routing_update_id.binary
            off += crypto.SHA256_HASH_LEN

            struct.pack_into("<I", self.buf, off, len(routing_update))
            off += constants.UL_INT_SIZE_IN_BYTES

            for node_id in routing_update:
                struct.pack_into("<16s", self.buf, off, uuid_pack.to_bytes(node_id))
                off += constants.NODE_ID_SIZE_IN_BYTES

    def __repr__(self):
        return (
            f"RoutingUpdateMessage<"
            f"message_hash: {self.message_hash()}, "
            f"origin_node_id: {self.origin_node_id()}, "
            f"forwarding_node_id: {self.origin_node_id()}, "
            f"routing_update_id: {self.routing_update()}, "
            f"routing_update: {self.routing_update()}, "
            f">"
        )

    def origin_node_id(self) -> str:
        if self._origin_node_id is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
            )
            origin_node_id = uuid_pack.from_bytes(
                struct.unpack_from("<16s", self.buf, off)[0]
            )
            self._origin_node_id = origin_node_id

        origin_node_id = self._origin_node_id
        assert origin_node_id is not None
        return origin_node_id

    def forwarding_node_id(self) -> str:
        if self._forwarding_node_id is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
                + constants.NODE_ID_SIZE_IN_BYTES
            )
            forwarding_node_id = uuid_pack.from_bytes(
                struct.unpack_from("<16s", self.buf, off)[0]
            )
            self._forwarding_node_id = forwarding_node_id

        forwarding_node_id = self._forwarding_node_id
        assert forwarding_node_id is not None
        return forwarding_node_id

    def routing_update_id(self) -> Sha256Hash:
        if self._routing_update_id is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
                + 2 * constants.NODE_ID_SIZE_IN_BYTES
            )
            self._routing_update_id = Sha256Hash(self._memoryview[off:off + crypto.SHA256_HASH_LEN])

        routing_update_id = self._routing_update_id
        assert routing_update_id is not None
        return routing_update_id

    def routing_update(self) -> List[str]:
        if self._routing_update is None:
            off = (
                self.HEADER_LENGTH
                + AbstractBroadcastMessage.PAYLOAD_LENGTH
                - constants.CONTROL_FLAGS_LEN
                + 2 * constants.NODE_ID_SIZE_IN_BYTES
                + crypto.SHA256_HASH_LEN
            )
            route_count, = struct.unpack_from("<I", self.buf, off)
            off += constants.UL_INT_SIZE_IN_BYTES

            routes = []
            for _ in range(route_count):
                route_id = uuid_pack.from_bytes(
                    struct.unpack_from("<16s", self.buf, off)[0]
                )
                off += constants.NODE_ID_SIZE_IN_BYTES
                routes.append(route_id)

            self._routing_update = routes

        routing_update = self._routing_update
        assert routing_update is not None
        return routing_update

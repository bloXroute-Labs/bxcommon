from cryptography import utils
from cryptography.x509.extensions import UnrecognizedExtension

from bxutils.ssl.extensions.extensions_object_ids import ExtensionsObjectIds


class NodeIdExtension(UnrecognizedExtension):

    def __init__(self, node_id: str) -> None:
        super(NodeIdExtension, self).__init__(ExtensionsObjectIds.NODE_ID, node_id.encode("utf-8"))
        self._node_id = node_id

    node_id = utils.read_only_property("_node_id")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <node_id: {self._node_id}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, NodeIdExtension):
            return NotImplemented

        return self._node_id == other._node_id

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return hash(self._node_id)

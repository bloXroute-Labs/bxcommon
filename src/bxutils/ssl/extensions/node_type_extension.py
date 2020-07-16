from cryptography import utils
from cryptography.x509.extensions import UnrecognizedExtension

from bxutils.ssl.extensions.extensions_object_ids import ExtensionsObjectIds


class NodeTypeExtension(UnrecognizedExtension):

    def __init__(self, node_type: str) -> None:
        super(NodeTypeExtension, self).__init__(ExtensionsObjectIds.NODE_TYPE, node_type.encode("utf-8"))
        self._node_type = node_type

    node_type = utils.read_only_property("_node_type")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <node_type: {self._node_type}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, NodeTypeExtension):
            return NotImplemented

        return self._node_type == other._node_type

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return hash(self._node_type)

from cryptography import utils
from cryptography.x509.extensions import UnrecognizedExtension

from bxutils.ssl.extensions.extensions_object_ids import ExtensionsObjectIds


class NodePrivilegesExtension(UnrecognizedExtension):

    def __init__(self, node_privileges: str) -> None:
        super().__init__(ExtensionsObjectIds.NODE_PRIVILEGES, node_privileges.encode("utf-8"))
        self._node_privileges = node_privileges

    node_privileges = utils.read_only_property("_node_privileges")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <node_privileges: {self._node_privileges}>"

    def __eq__(self, other) -> bool:
        if not isinstance(other, NodePrivilegesExtension):
            return NotImplemented

        return self._node_privileges == other._node_privileges

    def __ne__(self, other) -> bool:
        return not self == other

    def __hash__(self):
        return hash(self._node_privileges)

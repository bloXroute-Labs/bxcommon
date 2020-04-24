from typing import List, Optional, Union

from cryptography.x509 import BasicConstraints, Certificate, ExtensionNotFound, KeyUsage, \
    UnrecognizedExtension

from bxcommon.models.node_type import NodeType
from bxutils.ssl.extensions.account_id_extension import AccountIdExtension
from bxutils.ssl.extensions.extensions_object_ids import ExtensionsObjectIds
from bxutils.ssl.extensions.node_id_extension import NodeIdExtension
from bxutils.ssl.extensions.node_type_extension import NodeTypeExtension

DEFAULT_KEY_USAGE = KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            content_commitment=True,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
            key_cert_sign=False,
            crl_sign=False
)


def create_node_type_extension(node_type: NodeType) -> NodeTypeExtension:
    return NodeTypeExtension(node_type.name)


def create_node_id_extension(node_id: str) -> NodeIdExtension:
    return NodeIdExtension(node_id)


def create_account_id_extension(account_id: str) -> AccountIdExtension:
    return AccountIdExtension(account_id)


def get_node_type(cert: Certificate) -> Optional[NodeType]:
    try:
        # pyre-fixme[16]: `ExtensionType` has no attribute `value`.
        # pyre-fixme[6]: Expected `ObjectIdentifier` for 1st param but got
        #  `ObjectIdentifier`.
        node_type_str = cert.extensions.get_extension_for_oid(ExtensionsObjectIds.NODE_TYPE).value.value.decode("utf-8")
        return NodeType[node_type_str]
    except ExtensionNotFound:
        return None


def get_node_id(cert: Certificate) -> Optional[str]:
    try:
        # pyre-fixme[16]: `ExtensionType` has no attribute `value`.
        # pyre-fixme[6]: Expected `ObjectIdentifier` for 1st param but got
        #  `ObjectIdentifier`.
        return cert.extensions.get_extension_for_oid(ExtensionsObjectIds.NODE_ID).value.value.decode("utf-8")
    except ExtensionNotFound:
        return None


def get_account_id(cert: Certificate) -> Optional[str]:
    try:
        # pyre-fixme[16]: `ExtensionType` has no attribute `value`.
        # pyre-fixme[6]: Expected `ObjectIdentifier` for 1st param but got
        #  `ObjectIdentifier`.
        return cert.extensions.get_extension_for_oid(ExtensionsObjectIds.ACCOUNT_ID).value.value.decode("utf-8")
    except ExtensionNotFound:
        return None


def get_custom_extensions(
        node_type: Optional[NodeType] = None,
        node_id: Optional[str] = None,
        account_id: Optional[str] = None,
        ca_cert: bool = False,
        # pyre-fixme[11]: Annotation `KeyUsage` is not defined as a type.
        key_usage: KeyUsage = DEFAULT_KEY_USAGE
# pyre-fixme[11]: Annotation `BasicConstraints` is not defined as a type.
# pyre-fixme[11]: Annotation `KeyUsage` is not defined as a type.
# pyre-fixme[11]: Annotation `UnrecognizedExtension` is not defined as a type.
) -> List[Union[KeyUsage, UnrecognizedExtension, BasicConstraints]]:
    # pyre-fixme[11]: Annotation `BasicConstraints` is not defined as a type.
    # pyre-fixme[11]: Annotation `KeyUsage` is not defined as a type.
    # pyre-fixme[11]: Annotation `UnrecognizedExtension` is not defined as a type.
    extensions: List[Union[KeyUsage, UnrecognizedExtension, BasicConstraints]] = [
        BasicConstraints(ca=ca_cert, path_length=None),
        key_usage
    ]
    if node_type is not None:
        extensions.append(create_node_type_extension(node_type))
    if node_id is not None:
        extensions.append(create_node_id_extension(node_id))
    if account_id is not None:
        extensions.append(create_account_id_extension(account_id))
    return extensions

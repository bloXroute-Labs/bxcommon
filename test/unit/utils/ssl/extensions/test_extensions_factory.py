import uuid
import os

from bxcommon.models.node_type import NodeType
from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization
from cryptography.hazmat.primitives import serialization

from bxcommon.test_utils.abstract_test_case import AbstractTestCase

from bxutils.ssl.extensions import extensions_factory
from bxutils.ssl import ssl_certificate_factory


class ExtensionsFactoryTest(AbstractTestCase):

    def setUp(self) -> None:
        self.folder_path = os.path.dirname(os.path.dirname(__file__))
        self.cert_file_path = os.path.join(self.folder_path, "template_cert.pem")
        self.csr_file_path = os.path.join(self.folder_path, "template_csr.pem")
        self.key_file_path = os.path.join(self.folder_path, "template_key.pem")
        with open(self.cert_file_path, "rb") as template_cert_file:
            self.template_cert: x509.Certificate = x509.load_pem_x509_certificate(
                template_cert_file.read(), backends.default_backend()
            )
        with open(self.csr_file_path, "rb") as template_csr_file:
            self.template_csr: x509.CertificateSigningRequest = x509.load_pem_x509_csr(
                template_csr_file.read(), backends.default_backend()
            )
        with open(self.key_file_path, "rb") as template_key_file:
            self.template_key: EllipticCurvePrivateKeyWithSerialization = serialization.load_pem_private_key(
                template_key_file.read(), None, backends.default_backend()
            )

    def test_create_node_type_extension(self):
        node_type = NodeType.GATEWAY
        extension = extensions_factory.create_node_type_extension(node_type)
        self.assertEqual(node_type.name, extension.node_type)

    def test_create_node_id_extension(self):
        node_id = str(uuid.uuid4())
        extension = extensions_factory.create_node_id_extension(node_id)
        self.assertEqual(node_id, extension.node_id)

    def test_get_node_credentials(self):
        node_type = NodeType.GATEWAY
        node_id = str(uuid.uuid4())
        cert = ssl_certificate_factory.sign_csr(
            self.template_csr,
            self.template_cert,
            self.template_key,
            365,
            extensions_factory.get_custom_extensions(node_type, node_id)
        )
        self.assertEqual(node_type, extensions_factory.get_node_type(cert))
        self.assertEqual(node_id, extensions_factory.get_node_id(cert))

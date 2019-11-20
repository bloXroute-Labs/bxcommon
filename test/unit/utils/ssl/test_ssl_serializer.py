import os

from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

from bxcommon.test_utils.abstract_test_case import AbstractTestCase

from bxutils.ssl import ssl_serializer


class SSLSerializerTest(AbstractTestCase):

    def setUp(self) -> None:
        self.folder_path = os.path.dirname(__file__)
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

    def test_to_binary(self):
        text = "hello world"
        binary_text = text.encode("utf-8")
        self.assertEqual(binary_text, ssl_serializer.to_binary(binary_text))
        self.assertEqual(binary_text, ssl_serializer.to_binary(text))

    def test_deserialize_csr(self):
        with open(self.csr_file_path, "rb") as template_csr_file:
            csr = ssl_serializer.deserialize_csr(template_csr_file.read())
        self.assertEqual(self.template_csr, csr)

    def test_serialize_csr(self):
        with open(self.csr_file_path, "rb") as template_csr_file:
            raw_csr = template_csr_file.read().decode("utf-8")
        self.assertEqual(raw_csr, ssl_serializer.serialize_csr(self.template_csr))

    def test_deserialize_cert(self):
        with open(self.cert_file_path, "rb") as template_cert_file:
            cert = ssl_serializer.deserialize_cert(template_cert_file.read())
        self.assertEqual(self.template_cert, cert)

    def test_serialize_cert(self):
        with open(self.cert_file_path, "rb") as template_cert_file:
            raw_cert = template_cert_file.read().decode("utf-8")
        self.assertEqual(raw_cert, ssl_serializer.serialize_cert(self.template_cert))

    def test_deserialize_key(self):
        with open(self.key_file_path, "rb") as template_key_file:
            key = ssl_serializer.deserialize_key(template_key_file.read())
        self.assertEqual(
            self.template_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()),
            key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
        )

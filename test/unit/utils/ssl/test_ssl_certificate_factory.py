import os
from io import BytesIO
from tempfile import NamedTemporaryFile

from cryptography import x509
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
from cryptography.hazmat.primitives import serialization

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.test_utils import helpers

from bxutils.ssl import ssl_certificate_factory
from bxutils.common import url_helper


class MockFileStream(BytesIO):

    def __init__(self):
        super().__init__()
        self.data = None

    def write(self, data):
        self.data = data


class SSLCertificateFactoryTest(AbstractTestCase):

    def setUp(self) -> None:
        self.set_ssl_folder()
        self.file_path = "dummy_path"
        self.stream_mock = MockFileStream()
        self.cert_file_path = os.path.join(self.ssl_folder_path, "template_cert.pem")
        with open(self.cert_file_path, "rb") as template_cert_file:
            self.template_cert: x509.Certificate = x509.load_pem_x509_certificate(
                template_cert_file.read(), backends.default_backend()
            )

    def test_create_csr(self):
        key: ec.EllipticCurvePrivateKey = ec.generate_private_key(ec.SECP384R1(), backends.default_backend())
        csr = ssl_certificate_factory.create_csr(key, self.template_cert)
        self.assertEqual(self.template_cert.subject, csr.subject)
        self.assertEqual(
            key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo),
            csr.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        )
        key.public_key().verify(csr.signature, csr.tbs_certrequest_bytes, ec.ECDSA(csr.signature_hash_algorithm))
        self.assertTrue(csr.is_signature_valid)
        self.assertEqual(
            self.template_cert.extensions.get_extension_for_class(x509.SubjectAlternativeName),
            csr.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        )

    def test_generate_key(self):
        key = ssl_certificate_factory.generate_key()
        self.assertIsInstance(key, ec.EllipticCurvePrivateKeyWithSerialization)

    def test_store(self):
        data = helpers.generate_bytes(100)
        ssl_certificate_factory.store(self.file_path, data, self._stream_factory)
        self.assertEqual(data, self.stream_mock.data)

    def test_store_certificate(self):
        cert_name = "ref_cert"
        self.file_path = os.path.join(self.ssl_folder_path, ssl_certificate_factory.CERT_FILE_FORMAT.format(cert_name))
        ssl_certificate_factory.store_certificate(
            self.template_cert, self.ssl_folder_path, "ref_cert", self._stream_factory
        )
        self.assertEqual(
            self.template_cert,
            x509.load_pem_x509_certificate(self.stream_mock.data, backends.default_backend())
        )

    def test_store_key(self):
        key_name = "ref_key"
        key: ec.EllipticCurvePrivateKeyWithSerialization = ec.generate_private_key(
            ec.SECP384R1(), backends.default_backend()
        )
        self.file_path = os.path.join(self.ssl_folder_path, ssl_certificate_factory.KEY_FILE_FORMAT.format(key_name))
        ssl_certificate_factory.store_key(key, self.ssl_folder_path, key_name, self._stream_factory)
        ref_key = serialization.load_pem_private_key(self.stream_mock.data, None, backends.default_backend())
        self.assertEqual(
            key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()),
            ref_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
        )

    def test_fetch_cert(self):
        url = url_helper.url_join("file:", self.cert_file_path)
        cert = ssl_certificate_factory.fetch_cert(url)
        self.assertEqual(self.template_cert, cert)

    def test_fetch_key(self):
        key_name = "temp_key_file"
        key_file = NamedTemporaryFile()
        key = ssl_certificate_factory.generate_key()
        self.file_path = os.path.join(self.ssl_folder_path, ssl_certificate_factory.KEY_FILE_FORMAT.format(key_name))
        ssl_certificate_factory.store_key(key, self.ssl_folder_path, key_name, self._stream_factory)
        key_file.write(self.stream_mock.data)
        key_file.seek(0)
        ref_key = ssl_certificate_factory.fetch_key(url_helper.url_join("file:", key_file.name))
        self.assertEqual(
            key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()),
            ref_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
        )

    def test_sign_csr(self):
        ca_key = ssl_certificate_factory.fetch_key(url_helper.url_join(
            "file:",
            self.ssl_folder_path,
            "ca_key.pem"
        ))
        ca_cert = ssl_certificate_factory.fetch_cert(url_helper.url_join(
            "file:",
            self.ssl_folder_path,
            "ca_cert.pem"
        ))
        key = ssl_certificate_factory.fetch_key(url_helper.url_join(
            "file:",
            self.ssl_folder_path,
            "template_key.pem"
        ))
        csr = ssl_certificate_factory.create_csr(key, self.template_cert)
        cert = ssl_certificate_factory.sign_csr(
            csr, ca_cert, ca_key, 365, []
        )
        self.assertEqual(self.template_cert.issuer, cert.issuer)
        self.assertEqual(self.template_cert.subject, cert.subject)
        self.assertEqual(
            self.template_cert.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo),
            cert.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        )

    def _stream_factory(self, request_file_path):
        self.assertEqual(self.file_path, request_file_path)
        return self.stream_mock

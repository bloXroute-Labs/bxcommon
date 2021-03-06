import os
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from bxcommon.models.node_type import NodeType
from bxcommon.test_utils.abstract_test_case import AbstractTestCase

from bxutils.common import url_helper
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils.ssl import ssl_certificate_factory
from bxutils.ssl.data.ssl_certificate_info import SSLCertificateInfo
from bxutils.ssl.data.ssl_file_info import SSLFileInfo
from bxutils.ssl.data.ssl_storage_info import SSLStorageInfo
from bxutils.ssl.ssl_certificate_type import SSLCertificateType


class NodeSSLServiceTest(AbstractTestCase):
    def setUp(self) -> None:
        self.set_ssl_folder()
        self.ssl_folder_path = os.path.join(self.ssl_folder_path, "template")
        self.ssl_folder_url = url_helper.url_join("file:", self.ssl_folder_path)
        cert_name = "template_cert.pem"
        key_name = "template_key.pem"
        self.storage_info = SSLStorageInfo(
            self.ssl_folder_path,
            SSLCertificateInfo(
                SSLFileInfo("", cert_name, url_helper.url_join(self.ssl_folder_url, cert_name)),
                SSLFileInfo("", key_name, url_helper.url_join(self.ssl_folder_url, key_name))
            ),
            SSLCertificateInfo(
                SSLFileInfo("", cert_name),
                SSLFileInfo("", key_name)
            ),
            SSLCertificateInfo(
                SSLFileInfo("", cert_name, url_helper.url_join(self.ssl_folder_url, cert_name)),
                SSLFileInfo("", key_name, url_helper.url_join(self.ssl_folder_url, key_name))
            )
        )
        self.node_service = NodeSSLService(NodeType.API, self.storage_info, store_local=False)
        self.node_service.blocking_load()
        self.ref_cert = ssl_certificate_factory.fetch_cert(url_helper.url_join(self.ssl_folder_url, cert_name))
        self.ref_key = ssl_certificate_factory.fetch_key(url_helper.url_join(self.ssl_folder_url, key_name))

    def test_load(self):
        self.assertTrue(self.node_service.has_valid_certificate(SSLCertificateType.CA))
        self.assertEqual(self.ref_cert, self.node_service.get_certificate(SSLCertificateType.CA))
        self.assertTrue(self.node_service.has_valid_certificate(SSLCertificateType.REGISTRATION_ONLY))
        self.assertEqual(self.ref_cert, self.node_service.get_certificate(SSLCertificateType.REGISTRATION_ONLY))

    def test_create_csr(self):
        csr = self.node_service.create_csr()
        self.assertEqual(
            self.node_service.private_keys[SSLCertificateType.PRIVATE].public_key().public_bytes(
                Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
            ),
            csr.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        )

import asyncio
import os
import ssl
from datetime import datetime, timedelta
from ssl import Purpose, SSLContext
from typing import Dict, Iterator, Optional

from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKeyWithSerialization
from cryptography.x509 import Certificate, CertificateSigningRequest

from bxcommon.models.node_type import NodeType
from bxutils import constants, logging
from bxutils.common import url_helper
from bxutils.ssl import ssl_certificate_factory
from bxutils.ssl.data.ssl_file_info import SSLFileInfo
from bxutils.ssl.data.ssl_storage_info import SSLStorageInfo
from bxutils.ssl.extensions import extensions_factory
from bxutils.ssl.ssl_certificate_type import SSLCertificateType

logger = logging.get_logger(__name__)


def is_cert_valid(cert: Certificate, expiration_threshold_days: int = 0) -> bool:
    """
    Checking if a certificate is valid or will still be valid until `expiration_threshold_days` will pass.
    :param cert: the certificate to validate.
    :param expiration_threshold_days: the additional period (in days) in which the certificate should still be valid.
    :return: True if valid, otherwise False.
    """
    utc_now = datetime.utcnow()
    expiration_threshold = timedelta(days=expiration_threshold_days)
    return cert.not_valid_before <= utc_now + expiration_threshold <= cert.not_valid_after


class NodeSSLService:
    """
    A service class for a node that provides - fetching, loading, storing and creating cert chains.
    Pass store_local=False if storing cert the cert chains locally is not required (usually for testing).
    Typical usage is as follows:
        1. Create and load the NodeSSLService.
        2. Check if we should request for a new certificate using the should_renew_node_certificate method.
        3. If required, create a CSR, add it to the node registration request and store the private certificate.
        4. Create an SSLContext by calling create_ssl_context(SSLCertificateType.PRIVATE).
    """
    storage_info: SSLStorageInfo
    certificates: Dict[SSLCertificateType, Certificate]
    private_keys: Dict[SSLCertificateType, EllipticCurvePrivateKeyWithSerialization]
    _store_local: bool
    _node_name: str

    def __init__(self, node_type: NodeType, storage_info: SSLStorageInfo, store_local: bool = True) -> None:
        if storage_info.certificates_info[SSLCertificateType.PRIVATE].key_file_info is None:
            raise ValueError(f"Storage info {storage_info} is missing key file storage info for a private certificate.")
        self.storage_info = storage_info
        self.certificates = {}
        self.private_keys = {}
        self._node_name = node_type.name.lower()
        self._store_local = store_local

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <{self._node_name}>"

    def blocking_load(self) -> None:
        """
        Load the service in a blocking manner.
        CA and REGISTRATION_ONLY certificates will be fetched from their configured URLs.
        The PRIVATE certificate will be loaded if exists in the local path.
        Local directories will be created if needed.
        :raise RuntimeError: if either the CA certificate or the Node certificate is missing.
        """
        self._make_dirs()
        for cert_type, cert_info in self.storage_info.certificates_info.items():
            cert_file_info = cert_info.cert_file_info
            cert_url = self._get_url(cert_file_info)
            if cert_url is not None:
                logger.trace("Load ssl certificate {}", cert_url)
                cert = ssl_certificate_factory.fetch_cert(cert_url)
                self.certificates[cert_type] = cert
                self._store_cert(cert_type, cert)
            key_file_info = cert_info.key_file_info
            if key_file_info is not None:
                key_url = self._get_url(key_file_info)
                if key_url is not None:
                    logger.trace("Load ssl key {}", key_url)
                    key = ssl_certificate_factory.fetch_key(key_url)
                    self.private_keys[cert_type] = key
                    self._store_key(key, key_file_info)
        if not self.has_valid_certificate(SSLCertificateType.CA):
            raise RuntimeError("Failed to load CA certificate.")
        elif not self.has_valid_certificate(SSLCertificateType.REGISTRATION_ONLY) and not \
                self.has_valid_certificate(SSLCertificateType.PRIVATE):
            raise RuntimeError("Failed to load node certificate.")

        logger.info("{} is successfully loaded.", self)

    async def load(self) -> None:
        """
        Load the service in a non blocking manner.
        """
        loop = asyncio.get_event_loop()
        # TODO : convert to proper async
        await loop.run_in_executor(None, self.blocking_load)

    def get_certificate(self, cert_type: SSLCertificateType) -> Certificate:
        """
        Get a certificate from the chain according to a specific type.
        :param cert_type: The certificate type (CA, REGISTRATION_ONLY, PRIVATE) to get.
        :return: an SSL certificate object.
        :raise ValueError: if the requested certificate (cert_type) is missing.
        """
        try:
            return self.certificates[cert_type]
        except KeyError:
            raise ValueError(f"Could not find SSL certificate for type: {cert_type}.")

    def has_valid_certificate(self, cert_type: SSLCertificateType) -> bool:
        """
        Check if the service has a valid certificate for a specific type.
        :param cert_type: The certificate type (CA, REGISTRATION_ONLY, PRIVATE) to check.
        :return: True if has valid certificate, otherwise False.
        """
        return cert_type in self.certificates and is_cert_valid(self.certificates[cert_type])

    def has_invalid_certificate(self, cert_type: SSLCertificateType) -> bool:
        """
        Check if the service has an invalid certificate for a specific type.
        :param cert_type: The certificate type (CA, REGISTRATION_ONLY, PRIVATE) to check.
        :return: True if has a certificate and it is invalid, otherwise False.
        """
        return cert_type in self.certificates and not is_cert_valid(self.certificates[cert_type])

    def should_renew_node_certificate(
            self, expiration_threshold_days: int = constants.DEFAULT_CERTIFICATE_RENEWAL_PERIOD_DAYS
    ) -> bool:
        """
        Check if the service should renew its node private certificate.
        :param expiration_threshold_days: the threshold in days, in which a renewal should be requested.
        :return: True if renewal is required, otherwise False.
        """
        has_cert = SSLCertificateType.PRIVATE in self.certificates \
            and SSLCertificateType.REGISTRATION_ONLY in self.certificates
        if has_cert and is_cert_valid(self.certificates[SSLCertificateType.PRIVATE], expiration_threshold_days):
            private_account = extensions_factory.get_account_id(
                self.certificates[SSLCertificateType.PRIVATE]
            )
            registration_only_account = extensions_factory.get_account_id(
                self.certificates[SSLCertificateType.REGISTRATION_ONLY]
            )
            return private_account != registration_only_account

        return True

    def blocking_store_node_certificate(self, cert: Certificate) -> None:
        """
        Store a node private certificate in a blocking manner
        :param cert: the node private certificate to be stored.
        """
        key = self.private_keys[SSLCertificateType.PRIVATE]
        if self._store_local:
            ssl_folder_path = self.storage_info.ssl_folder_path
            key_file_info = self.storage_info.certificates_info[SSLCertificateType.PRIVATE].key_file_info
            key_folder_path = os.path.join(ssl_folder_path, key_file_info.sub_directory_name)  # pyre-ignore
            ssl_certificate_factory.store_key(key, key_folder_path, self._node_name)
        self.certificates[SSLCertificateType.PRIVATE] = cert
        self._store_cert(SSLCertificateType.PRIVATE, cert)
        node_id = extensions_factory.get_node_id(cert)
        logger.debug("{} successfully stored private SSL certificate: {} ({}).", self, cert, node_id)

    async def store_node_certificate(self, cert: Certificate) -> None:
        """
        Store a node private certificate in a non blocking manner
        :param cert: the node private certificate to be stored.
        """
        loop = asyncio.get_event_loop()
        # TODO : convert to proper async
        await loop.run_in_executor(None, self.blocking_store_node_certificate, cert)

    def create_csr(self) -> CertificateSigningRequest:
        """
        Create a Certificate Signing Request (CSR) for a private node certificate.
        :return: CSR (https://en.wikipedia.org/wiki/Certificate_signing_request)
        """
        key = ssl_certificate_factory.generate_key()
        self.private_keys[SSLCertificateType.PRIVATE] = key
        template_cert = self.certificates[SSLCertificateType.REGISTRATION_ONLY]
        csr = ssl_certificate_factory.create_csr(key, template_cert)
        logger.debug("{} successfully created private SSL CSR: {}.", self, csr)
        return csr

    def create_ssl_context(self, cert_type: SSLCertificateType) -> SSLContext:
        """
        Create an SSL context object to be used for wrapping SSLSockets
        (https://docs.python.org/3.7/library/ssl.html#ssl.SSLSocket).
        :param cert_type: the certificate type to use when creating the context.
        :return: an SSL context object (https://docs.python.org/3.7/library/ssl.html#ssl.SSLContext)
        """
        cert_info = self.storage_info.certificates_info[cert_type]
        context = ssl.create_default_context(
            Purpose.SERVER_AUTH,
            cafile=self._get_file_path(self.storage_info.certificates_info[SSLCertificateType.CA].cert_file_info)
        )
        context.load_cert_chain(
            self._get_file_path(cert_info.cert_file_info), self._get_file_path(cert_info.key_file_info)  # pyre-ignore
        )
        context.check_hostname = False
        logger.debug(
            "{} successfully created SSL context for certificate: {}.",
            self,
            self.certificates[cert_type]
        )
        return context

    def get_node_id(self) -> str:
        cert = self.get_certificate(SSLCertificateType.PRIVATE)
        node_id = extensions_factory.get_node_id(cert)
        if node_id is None:
            raise TypeError(f"Node id is missing in private certificate: {cert}!")
        return node_id

    def get_account_id(self) -> Optional[str]:
        cert = None
        try:
            cert = self.get_certificate(SSLCertificateType.REGISTRATION_ONLY)
        except ValueError:
            pass
        if cert is None:
            logger.info("Could not find SSL certificate, continue without account settings")
            return None
        account_id = extensions_factory.get_account_id(cert)
        if account_id is None:
            logger.info("Account id is missing in certificate: {}!", cert)
        return account_id

    def _store_cert(self, cert_type: SSLCertificateType, cert: Certificate) -> None:
        if not self._store_local:
            logger.debug("{} skip saving {} to local storage.", self, cert)
            return
        cert_file_info = self.storage_info.certificates_info[cert_type].cert_file_info
        cert_folder_path = os.path.join(
            self.storage_info.ssl_folder_path, cert_file_info.sub_directory_name
        )
        cert_file_name = cert_type.name.lower() if cert_type == SSLCertificateType.CA else self._node_name
        ssl_certificate_factory.store_certificate(cert, cert_folder_path, cert_file_name)

    def _store_key(self, key: EllipticCurvePrivateKeyWithSerialization, file_info: Optional[SSLFileInfo]) -> None:
        if not self._store_local or file_info is None:
            logger.debug("{} skip saving private key to local storage.", self)
            return
        ssl_folder_path = self.storage_info.ssl_folder_path
        folder_path = os.path.join(ssl_folder_path, file_info.sub_directory_name)
        file_parts = file_info.file_name.split("_")[:-1]
        file_prefix = "_".join(file_parts)
        ssl_certificate_factory.store_key(key, folder_path, file_prefix)

    def _make_dirs(self) -> None:
        if not self._store_local:
            return
        ssl_folder_path = self.storage_info.ssl_folder_path

        def _get_dirs() -> Iterator[str]:
            yield ssl_folder_path
            for cert_info in self.storage_info.certificates_info.values():
                yield os.path.join(ssl_folder_path, cert_info.cert_file_info.sub_directory_name)
        for folder_path in _get_dirs():
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                logger.debug("{} creating missing directory: {}.", self, folder_path)

    def _get_url(self, file_info: SSLFileInfo) -> Optional[str]:
        url = file_info.url
        file_path = self._get_file_path(file_info)
        if url is None and self._store_local and os.path.exists(file_path):
            return url_helper.url_join("file:", file_path)
        else:
            return url

    def _get_file_path(self, file_info: SSLFileInfo) -> str:
        ssl_folder_path = self.storage_info.ssl_folder_path
        return os.path.join(ssl_folder_path, file_info.sub_directory_name, file_info.file_name)

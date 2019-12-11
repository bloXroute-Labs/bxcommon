from ssl import SSLContext

from bxutils.services.node_ssl_service import NodeSSLService
from bxutils.ssl.ssl_certificate_type import SSLCertificateType


class MockNodeSSLService(NodeSSLService):

    def blocking_load(self) -> None:
        pass

    def create_ssl_context(self, cert_type: SSLCertificateType) -> SSLContext:
        pass


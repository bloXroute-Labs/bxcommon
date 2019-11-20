from typing import Dict, Optional

from bxutils.ssl.data.ssl_certificate_info import SSLCertificateInfo
from bxutils.ssl.ssl_certificate_type import SSLCertificateType


class SSLStorageInfo:
    ssl_folder_path: str
    certificates_info: Dict[SSLCertificateType, SSLCertificateInfo]

    def __init__(
            self,
            ssl_folder_path: str,
            ca_cert_info: SSLCertificateInfo,
            private_cert_info: SSLCertificateInfo,
            registration_cert_info: Optional[SSLCertificateInfo] = None,
     ):
        self.ssl_folder_path = ssl_folder_path
        self.certificates_info = {
            SSLCertificateType.CA: ca_cert_info,
            SSLCertificateType.PRIVATE: private_cert_info
        }
        if registration_cert_info is not None:
            self.certificates_info[SSLCertificateType.REGISTRATION_ONLY] = registration_cert_info

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <" \
            f"ssl_folder_path = {self.ssl_folder_path}, " \
            f"certificates_info = {self.certificates_info}" \
            f">"

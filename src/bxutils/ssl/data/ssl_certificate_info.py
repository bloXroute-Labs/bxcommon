from typing import NamedTuple, Optional

from bxutils.ssl.data.ssl_file_info import SSLFileInfo


class SSLCertificateInfo(NamedTuple):
    cert_file_info: SSLFileInfo
    key_file_info: Optional[SSLFileInfo] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <" \
            f"cert_file_info = {self.cert_file_info}, " \
            f"key_file_info = {self.key_file_info}" \
            f">"

import os
from typing import Optional

from bxcommon.models.node_type import NodeType
from bxutils import constants
from bxutils.common import url_helper
from bxutils.ssl.data.ssl_certificate_info import SSLCertificateInfo
from bxutils.ssl.data.ssl_file_info import SSLFileInfo
from bxutils.ssl.data.ssl_storage_info import SSLStorageInfo
from bxutils.ssl.ssl_certificate_type import SSLCertificateType

CA_DIR_NAME: str = SSLCertificateType.CA.name.lower()
REGISTRATION_DIR_NAME: str = SSLCertificateType.REGISTRATION_ONLY.name.lower()
PRIVATE_DIR_NAME: str = SSLCertificateType.PRIVATE.name.lower()


def get_cert_file_name(node_type: NodeType) -> str:
    node_name = node_type.name.lower()
    return constants.SSL_CERT_FILE_FORMAT.format(node_name)


def get_key_file_name(node_type: NodeType) -> str:
    node_name = node_type.name.lower()
    return constants.SSL_KEY_FILE_FORMAT.format(node_name)


def create_storage_info(
    *,
    node_type: NodeType,
    is_ca: bool = False,
    ca_cert_url: Optional[str] = None,
    private_ssl_base_url: Optional[str] = None,
    data_dir: str,
    ca_dir_name: str = CA_DIR_NAME,
    registration_dir_name: str = REGISTRATION_DIR_NAME,
    private_dir_name: str = PRIVATE_DIR_NAME
) -> SSLStorageInfo:
    node_name = node_type.name.lower()
    node_ssl_directory = os.path.join(data_dir, constants.SSL_FOLDER, node_name)

    if ca_cert_url is None or private_ssl_base_url is None:
        ca_cert_url = url_helper.url_join("file:", node_ssl_directory, SSLCertificateType.CA.name.lower())
        private_ssl_base_url = url_helper.url_join("file:", node_ssl_directory)
        node_base_url = private_ssl_base_url
    else:
        node_base_url = url_helper.url_join(private_ssl_base_url, node_name)

    ca_cert_name = constants.SSL_CERT_FILE_FORMAT.format(ca_dir_name)
    if is_ca:
        ca_key_name = constants.SSL_KEY_FILE_FORMAT.format(ca_dir_name)
        ca_key_base_url = url_helper.url_join(private_ssl_base_url, ca_dir_name)
        ca_key_info = SSLFileInfo(
            ca_dir_name,
            ca_key_name,
            url_helper.url_join(ca_key_base_url, ca_key_name)
        )
    else:
        ca_key_info = None

    cert_file_name = get_cert_file_name(node_type)
    key_file_name = get_key_file_name(node_type)
    return SSLStorageInfo(
        node_ssl_directory,
        SSLCertificateInfo(
            SSLFileInfo(
                ca_dir_name,
                ca_cert_name,
                url_helper.url_join(ca_cert_url, ca_cert_name)
            ),
            ca_key_info
        ),
        SSLCertificateInfo(
            SSLFileInfo(
                private_dir_name,
                cert_file_name
            ),
            SSLFileInfo(
                private_dir_name,
                key_file_name
            )
        ),
        SSLCertificateInfo(
            SSLFileInfo(
                registration_dir_name,
                cert_file_name,
                url_helper.url_join(node_base_url, registration_dir_name, cert_file_name)
            ),
            SSLFileInfo(
                registration_dir_name,
                key_file_name,
                url_helper.url_join(node_base_url, registration_dir_name, key_file_name)
            )
        )
    )


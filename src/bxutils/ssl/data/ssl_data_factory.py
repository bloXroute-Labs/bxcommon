import os

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


def create_storage_info(
            *,
            node_type: NodeType,
            is_ca: bool = False,
            is_public_node: bool = True,
            public_ssl_url: str = constants.DEFAULT_PUBLIC_SSL_BASE_URL,
            private_ssl_url: str = constants.DEFAULT_PRIVATE_SSL_BASE_URL,
            ssl_folder_path: str = constants.DEFAULT_SSL_FOLDER_PATH,
            ca_dir_name: str = CA_DIR_NAME,
            registration_dir_name: str = REGISTRATION_DIR_NAME,
            private_dir_name: str = PRIVATE_DIR_NAME
) -> SSLStorageInfo:
    node_name = node_type.name.lower()
    node_ssl_directory = os.path.join(ssl_folder_path, node_name)
    public_ssl_url = url_helper.url_join(public_ssl_url, node_name)
    private_ssl_url = url_helper.url_join(private_ssl_url, node_name)
    ca_cert_name = constants.SSL_CERT_FILE_FORMAT.format(ca_dir_name)
    ca_base_url = url_helper.url_join(public_ssl_url, ca_dir_name)
    if is_ca:
        ca_key_name = constants.SSL_KEY_FILE_FORMAT.format(ca_dir_name)
        ca_key_base_url = url_helper.url_join(private_ssl_url, ca_dir_name)
        ca_key_info = SSLFileInfo(
            ca_dir_name,
            ca_key_name,
            url_helper.url_join(ca_key_base_url, ca_key_name)
        )
    else:
        ca_key_info = None
    if is_public_node:
        node_base_url = public_ssl_url
    else:
        node_base_url = private_ssl_url
    registration_cert_name = constants.SSL_CERT_FILE_FORMAT.format(node_name)
    registration_key_name = constants.SSL_KEY_FILE_FORMAT.format(node_name)
    return SSLStorageInfo(
        node_ssl_directory,
        SSLCertificateInfo(
            SSLFileInfo(
                ca_dir_name,
                ca_cert_name,
                url_helper.url_join(ca_base_url, ca_cert_name)
            ),
            ca_key_info
        ),
        SSLCertificateInfo(
            SSLFileInfo(
                private_dir_name,
                constants.SSL_CERT_FILE_FORMAT.format(node_name)
            ),
            SSLFileInfo(
                private_dir_name,
                constants.SSL_KEY_FILE_FORMAT.format(node_name)
            )
        ),
        SSLCertificateInfo(
            SSLFileInfo(
                registration_dir_name,
                registration_cert_name,
                url_helper.url_join(node_base_url, registration_dir_name, registration_cert_name)
            ),
            SSLFileInfo(
                registration_dir_name,
                registration_key_name,
                url_helper.url_join(node_base_url, registration_dir_name, registration_key_name)
            )
        )
    )

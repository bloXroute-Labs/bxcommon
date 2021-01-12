import argparse
import os
import unittest
from typing import Optional

from mock import MagicMock
from prometheus_client import REGISTRY

from bxcommon import node_runner
from bxcommon.models.node_type import NodeType
from bxcommon.services import http_service
from bxcommon.test_utils import helpers
from bxcommon.utils import cli
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxutils.common import url_helper
from bxutils.logging import log_config
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_record_type import LogRecordType
from bxutils.services.node_ssl_service import NodeSSLService
from bxutils.ssl.data import ssl_data_factory
from bxutils.ssl.data.ssl_certificate_info import SSLCertificateInfo
from bxutils.ssl.data.ssl_file_info import SSLFileInfo
from bxutils.ssl.data.ssl_storage_info import SSLStorageInfo

RELATIVE_PATH_SSL_FILES = "bxcommon/test/ssl_files"


def get_ssl_test_files(abs_path: str, relative_path_ssl_files: str) -> str:
    # walk backwards to root till find the "ssl_files" folder
    while abs_path is not None:
        abs_path, _tail = os.path.split(abs_path)
        if os.path.exists(os.path.join(abs_path, relative_path_ssl_files)):
            break
    return os.path.join(abs_path, relative_path_ssl_files)


class AbstractTestCase(unittest.TestCase):
    ssl_folder_path: str = ""
    ssl_folder_url: str = ""

    @classmethod
    def setUpClass(cls):
        arg_parser = argparse.ArgumentParser(add_help=False)
        cli.add_argument_parser_logging(arg_parser, default_log_level=LogLevel.DEBUG)
        opts = arg_parser.parse_args(args=[])
        log_config.setup_logging(
            opts.log_format,
            opts.log_level,
            default_logger_names=["bxcommon", "bxgateway", "bxrelay", "bxgateway_internal", "bxapi"],
            log_level_overrides=opts.log_level_overrides,
            enable_fluent_logger=opts.log_fluentd_enable,
            fluentd_host=opts.log_fluentd_host,
            fluentd_queue_size=opts.log_fluentd_queue_size,
            third_party_loggers=node_runner.THIRD_PARTY_LOGGERS,
            fluent_log_level=opts.log_level_fluentd,
            stdout_log_level=opts.log_level_stdout,
        )
        log_config.set_level([LogRecordType.Config.value], LogLevel.WARNING)

        http_service.get_json = MagicMock()
        http_service.post_json = MagicMock()
        http_service.patch_json = MagicMock()
        http_service.delete_json = MagicMock()
        memory_statistics.start_recording = MagicMock()

        REGISTRY.register = MagicMock()
        helpers.set_extensions_parallelism()

    def set_ssl_folder(self) -> None:
        self.ssl_folder_path = get_ssl_test_files(
            os.path.abspath(__file__), RELATIVE_PATH_SSL_FILES
        )
        self.ssl_folder_url = url_helper.url_join("file:", self.ssl_folder_path)

    def create_ssl_service(
        self, node_type: NodeType, ca_folder: str = "ca", node_folder: Optional[str] = None
    ) -> NodeSSLService:
        if node_folder is None:
            node_folder = node_type.name.lower()

        self.set_ssl_folder()

        cert_file_name = ssl_data_factory.get_cert_file_name(node_type)
        key_file_name = ssl_data_factory.get_key_file_name(node_type)
        ca_base_url = url_helper.url_join(
            self.ssl_folder_url, ca_folder
        )
        registration_base_url = url_helper.url_join(
            self.ssl_folder_url, node_folder, "registration_only"
        )
        node_ssl_service = NodeSSLService(
            node_type,
            SSLStorageInfo(
                self.ssl_folder_path,
                SSLCertificateInfo(
                    SSLFileInfo(
                        ca_folder,
                        "ca_cert.pem",
                        url_helper.url_join(ca_base_url, "ca_cert.pem"),

                    ),
                    SSLFileInfo(
                        ca_folder,
                        "ca_key.pem",
                        url_helper.url_join(ca_base_url, "ca_key.pem"),
                    )
                ),
                SSLCertificateInfo(
                    SSLFileInfo(
                        f"{node_folder}/private",
                        cert_file_name
                    ),
                    SSLFileInfo(
                        f"{node_folder}/private",
                        key_file_name
                    )
                ),
                SSLCertificateInfo(
                    SSLFileInfo(
                        f"{node_folder}/registration_only",
                        cert_file_name,
                        url_helper.url_join(registration_base_url, cert_file_name),
                    ),
                    SSLFileInfo(
                        f"{node_folder}/registration_only",
                        key_file_name,
                        url_helper.url_join(registration_base_url, key_file_name),
                    )
                )
            )
        )

        node_ssl_service.blocking_load()
        return node_ssl_service

    def assert_almost_equal(
        self,
        expected_value: float,
        actual_value: float,
        allowed_error: float = 0.001
    ):
        self.assertTrue(
            abs(expected_value - actual_value) <= allowed_error,
            msg=f"Expected {expected_value}, but "
                f"{actual_value} was more than {allowed_error} away."
        )

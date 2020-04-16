import os
import unittest

from mock import MagicMock
from prometheus_client import REGISTRY

from bxcommon.services import http_service
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxutils.common import url_helper
from bxutils.logging import log_config
from bxutils.logging.log_level import LogLevel
from bxutils.logging.log_record_type import LogRecordType

RELATIVE_PATH_SSL_FILES = "bxcommon/test/ssl_files"


# pyre-fixme[13]: Attribute `ssl_folder_path` is never initialized.
# pyre-fixme[13]: Attribute `ssl_folder_url` is never initialized.
class AbstractTestCase(unittest.TestCase):
    ssl_folder_path: str
    ssl_folder_url: str

    @classmethod
    def setUpClass(cls):
        log_config.create_logger(None)
        log_config.set_level([LogRecordType.Config.value], LogLevel.WARNING)
        log_config.set_level(["bxcommon", "bxgateway", "bxrelay", "bxgateway_internal"], LogLevel.DEBUG)
        http_service.get_json = MagicMock()
        http_service.post_json = MagicMock()
        http_service.patch_json = MagicMock()
        http_service.delete_json = MagicMock()
        memory_statistics.start_recording = MagicMock()

        REGISTRY.register = MagicMock()

    def set_ssl_folder(self) -> None:
        self.ssl_folder_path = self.get_ssl_test_files(os.path.abspath(__file__), RELATIVE_PATH_SSL_FILES)
        self.ssl_folder_url = url_helper.url_join("file:", self.ssl_folder_path)

    @staticmethod
    def get_ssl_test_files(abs_path: str, relative_path_ssl_files: str) -> str:
        # walk backwards to root till find the "ssl_files" folder
        while abs_path is not None:
            abs_path, tail = os.path.split(abs_path)
            if os.path.exists(os.path.join(abs_path, relative_path_ssl_files)):
                break
        return os.path.join(abs_path, relative_path_ssl_files)

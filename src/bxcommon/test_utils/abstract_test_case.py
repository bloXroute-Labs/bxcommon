import unittest
from mock import MagicMock

from bxutils.logging import log_config

from bxcommon.services import http_service
from bxcommon.utils.stats.memory_statistics_service import memory_statistics


class AbstractTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        log_config.create_logger(None)
        http_service.get_json = MagicMock()
        http_service.post_json = MagicMock()
        http_service.patch_json = MagicMock()
        http_service.delete_json = MagicMock()
        memory_statistics.start_recording = MagicMock()

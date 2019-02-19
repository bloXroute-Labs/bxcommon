import unittest

from mock import MagicMock

from bxcommon.utils import logger
from bxcommon.utils.stats.memory_statistics_service import memory_statistics


class AbstractTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.log_init(None, use_stdout=True)
        logger.set_immediate_flush(True)
        memory_statistics.start_recording = MagicMock()

    @classmethod
    def tearDownClass(cls):
        logger.log_close()

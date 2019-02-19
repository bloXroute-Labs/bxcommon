import unittest

from mock import MagicMock

from bxcommon.utils import logger
from bxcommon.utils.stats.memory_statistics_service import memory_statistics


class QuietTestCase(unittest.TestCase):
    """
    The log output from Gateway and Relay nodes tends to overwhelm all other output. This turns that off.
    Test output should just be `print`ed normally if using this base class.

    Tweak this as necessary for local debug.
    """

    @classmethod
    def setUpClass(cls):
        logger._log_level = logger.LogLevel.FATAL
        logger.log_init("./logs/", False)
        memory_statistics.start_recording = MagicMock()

    @classmethod
    def tearDownClass(cls):
        logger.log_close()

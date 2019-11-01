import unittest
from mock import MagicMock

from bxutils.logging import log_config
from bxutils.logging.log_level import LogLevel

from bxcommon.utils.stats.memory_statistics_service import memory_statistics


class QuietTestCase(unittest.TestCase):
    """
    The log output from Gateway and Relay nodes tends to overwhelm all other output. This turns that off.
    Test output should just be `print`ed normally if using this base class.

    Tweak this as necessary for local debug.
    """

    @classmethod
    def setUpClass(cls):
        log_config.create_logger(None, log_level=LogLevel.FATAL, folder_path="./logs/")
        memory_statistics.start_recording = MagicMock()

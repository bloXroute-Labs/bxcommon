from mock import MagicMock

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.utils.stats.memory_statistics_service import memory_statistics
from bxutils.logging import log_config
from bxutils.logging.log_level import LogLevel


class QuietTestCase(AbstractTestCase):
    """
    The log output from Gateway and Relay nodes tends to overwhelm all other output. This turns that off.
    Test output should just be `print`ed normally if using this base class.

    Tweak this as necessary for local debug.
    """

    @classmethod
    def setUpClass(cls):
        log_config.create_logger(None, root_log_level=LogLevel.FATAL, folder_path="./logs/")
        memory_statistics.start_recording = MagicMock()

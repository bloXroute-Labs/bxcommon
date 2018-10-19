import unittest

from bxcommon.utils import logger


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

    @classmethod
    def tearDownClass(cls):
        logger.log_close()

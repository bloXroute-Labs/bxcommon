import unittest

from bxcommon.utils import logger


class AbstractTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.log_init(None, use_stdout=True)
        logger.set_immediate_flush(True)

    @classmethod
    def tearDownClass(cls):
        logger.log_close()

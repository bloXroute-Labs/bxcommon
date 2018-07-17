import unittest
from bxcommon import constants

from bxcommon.utils import logger

class AbstractTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        #logger.log_init(None, use_stdout=True)
        pass

    @classmethod
    def tearDownClass(cls):
        #logger.log_close()
        pass

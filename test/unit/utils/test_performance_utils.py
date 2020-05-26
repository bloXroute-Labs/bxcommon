import time
from datetime import datetime
from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxutils import logging
from bxutils.logging import CustomLogger
from bxcommon.utils.performance_utils import log_operation_duration
from mock import patch

logger = logging.get_logger(__name__)

test_logger = logging.get_logger(__name__, "test")


class PerformanceUtilsTests(AbstractTestCase):
    start_time = 10

    @patch("bxcommon.utils.performance_utils.time.time")
    def test_log_operation_duration(self, mock_time):
        details = ("Hello"
                   "World")
        mock_time.return_value = 12

        log_operation_duration(
            test_logger,
            "Responsiveness Check",
            self.start_time,
            .5,
            details=details
    )

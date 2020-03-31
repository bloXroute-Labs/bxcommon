from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from logging import Formatter, LogRecord
from bxutils import logging
from bxutils.logging import log_config
from bxutils.logging import log_format
from bxutils import log_messages
import json
import io

import unittest


class JsonFormatterTesting(AbstractTestCase):
    def setUp(self) -> None:
        log_config.setup_logging(
            log_format=log_config.LogFormat.JSON,
            default_log_level=log_config.LogLevel.DEBUG,
            default_logger_names="",
            log_level_overrides={}
        )

    def test_logging(self):
        logger = logging.get_logger("test_logging")
        with self.assertLogs() as cm:
            logger.warning("TEST")
        self.assertEqual("WARNING:test_logging:TEST", cm.output[0])

    def test_json_formatter_item_order(self):
        formatter = log_format.JSONFormatter()
        log_record = LogRecord(
            __name__,
            logging.log_level.LogLevel.DEBUG,
            "",
            0,
            "test",
            (),
            None
        )
        msg_ = json.loads(formatter.format(log_record))
        msg_list = list(msg_.items())
        self.assertEqual(msg_list[0][0], "timestamp")
        self.assertEqual(msg_list[1][0], "level")

    def test_json_formatter_log_messages(self):
        formatter = log_format.JSONFormatter()
        log_record = LogRecord(
            name=__name__,
            level=logging.log_level.LogLevel.WARNING,
            pathname="",
            lineno=0,
            msg=log_messages.BDN_RETURNED_NO_PEERS,
            args="a",
            exc_info=None
        )
        msg_ = json.loads(formatter.format(log_record))
        self.assertIn("code", msg_)
        self.assertIsNotNone(msg_["code"])
        self.assertIn("category", msg_)
        self.assertIsNotNone(msg_["category"])

    def test_json_fluent_formatter_log_messages(self):
        formatter = log_format.FluentJSONFormatter()
        log_record = LogRecord(
            name=__name__,
            level=logging.log_level.LogLevel.WARNING,
            pathname="",
            lineno=0,
            msg=log_messages.BDN_RETURNED_NO_PEERS,
            args="a",
            exc_info=None
        )
        msg_ = formatter.format(log_record)
        self.assertIn("code", msg_)
        self.assertIsNotNone(msg_["code"])
        self.assertIn("category", msg_)
        self.assertIsNotNone(msg_["category"])



if __name__ == '__main__':
    unittest.main()

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from bxcommon.connections.connection_type import ConnectionType
from logging import Formatter, LogRecord
from bxutils.logging.formatters import FluentJSONFormatter
from bxutils import logging
from bxutils.logging import log_config
from bxutils.logging import formatters
from bxutils.logging.log_level import LogLevel
from bxutils import log_messages
from bxutils.encoding import json_encoder

import msgpack
import json


import unittest


class JsonFormatterTest(AbstractTestCase):
    def setUp(self) -> None:
        log_config.setup_logging(
            log_format=log_config.LogFormat.JSON,
            default_log_level=log_config.LogLevel.TRACE,
            default_logger_names="",
            log_level_overrides={}
        )

    def test_logging(self):
        logger = logging.get_logger("test_logging")
        with self.assertLogs() as cm:
            logger.warning("TEST {}", 1)
        self.assertEqual("WARNING:test_logging:TEST 1", cm.output[0])
        with self.assertLogs(level=logging.LogLevel.TRACE) as cm:
            logger.trace("TEST {}", 1)
        self.assertEqual("TRACE:test_logging:TEST 1", cm.output[0])
        with self.assertLogs(level=logging.LogLevel.WARNING) as cm:
            logger.warning(log_messages.BDN_RETURNED_NO_PEERS, 1)
        self.assertEqual("WARNING:test_logging:BDN returned no peers at endpoint: 1",
                         cm.output[0])

    def test_json_formatter_item_order(self):
        formatter = formatters.JSONFormatter()
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


class JsonFluentdFormatterTesting(AbstractTestCase):
    def setUp(self) -> None:
        self.formatter = FluentJSONFormatter()

    def test_logging(self):
        formatted_record = self.formatter.format(
            LogRecord(
                name=__name__,
                level=LogLevel.DEBUG,
                pathname="",
                lineno=0,
                msg={ConnectionType: 1},
                args=(),
                exc_info=None
            )
        )
        self.assertIsInstance(formatted_record, dict)
        print(formatted_record)

    def test_msgpack_encode_custom_objects(self):
        packed = msgpack.packb(
            {"key": ConnectionType.GATEWAY},
            default=json_encoder.EnhancedJSONEncoder().default
        )
        self.assertEqual(msgpack.unpackb(packed),
                         {"key": str(ConnectionType.GATEWAY)})

        packed = msgpack.packb(
            {ConnectionType.GATEWAY: 1},
            default=json_encoder.EnhancedJSONEncoder().default
        )
        self.assertEqual(msgpack.unpackb(packed),
                         {str(ConnectionType.GATEWAY): 1})


if __name__ == '__main__':
    unittest.main()

from bxcommon.test_utils.abstract_test_case import AbstractTestCase
from logging import StreamHandler
from bxutils import logging
from bxutils.logging import handler_type
from bxutils.logging import log_config
from bxutils.logging import formatters
from aiofluent.handler import FluentHandler
from bxutils.logging import fluentd_logging_helpers
import io
import unittest
import msgpack


class LogConfigTest(AbstractTestCase):
    def setUp(self) -> None:
        pass

    def _get_handlers(self, logger):
        handlers = []
        while logger.hasHandlers():
            handlers.extend(logger.handlers)
            if logger.propagate:
                logger = logger.parent
            else:
                break
        return handlers

    def test_create_logger(self):
        log_config.setup_logging(
            log_format=log_config.LogFormat.JSON,
            default_log_level=log_config.LogLevel.TRACE,
            default_logger_names="",
            log_level_overrides={}
        )

        logger = logging.get_logger("test_logging")
        handlers = self._get_handlers(logger)
        self.assertEqual(len(handlers), 1)
        for handler in handlers:
            self.assertIsInstance(handler, StreamHandler)
            self.assertIsInstance(handler.formatter, formatters.JSONFormatter)

    def test_create_logger_fluentd(self):
        log_config.setup_logging(
            log_format=log_config.LogFormat.JSON,
            default_log_level=log_config.LogLevel.TRACE,
            default_logger_names="",
            log_level_overrides={},
            enable_fluent_logger=True,
            fluentd_host="fluentd"
        )
        logger = logging.get_logger("test_logging")
        handlers = self._get_handlers(logger)
        self.assertEqual(len(handlers), 2)
        stream_handlers = [handler for handler in handlers if isinstance(handler, StreamHandler)]
        fluentd_handlers = [handler for handler in handlers if isinstance(handler, FluentHandler)]
        self.assertEqual(len(stream_handlers), 1)
        self.assertEqual(len(fluentd_handlers), 1)
        for handler in handlers:
            self.assertEqual(handler.level, 0)

        fluentd_handler = fluentd_handlers[0]
        stream_handler = stream_handlers[0]
        self.assertIsInstance(fluentd_handler.formatter, formatters.JSONFormatter)
        self.assertIsInstance(stream_handler.formatter, formatters.JSONFormatter)

    def test_custom_logger(self):
        log_config.setup_logging(
            log_format=log_config.LogFormat.JSON,
            default_log_level=log_config.LogLevel.TRACE,
            default_logger_names="",
            log_level_overrides={},
            enable_fluent_logger=True,
            fluentd_host="fluentd",
            third_party_loggers=[
                logging.LoggerConfig(
                    "test_logging", "{", logging.LogLevel.TRACE, handler_type.HandlerType.Fluent
                )]
        )
        logger = logging.get_logger("test_logging")
        handlers = self._get_handlers(logger)
        self.assertEqual(len(handlers), 1)
        stream_handlers = [handler for handler in handlers if isinstance(handler, StreamHandler)]
        fluentd_handlers = [handler for handler in handlers if isinstance(handler, FluentHandler)]
        self.assertEqual(len(stream_handlers), 0)
        self.assertEqual(len(fluentd_handlers), 1)
        for handler in handlers:
            self.assertEqual(handler.level, 0)

        fluentd_handler = fluentd_handlers[0]
        self.assertIsInstance(fluentd_handler.formatter, formatters.FluentJSONFormatter)

    def test_buffer_overflow_print(self):
        pending_records = b""
        records = []
        for i in range(10):
            record = {"key": i}
            pending_records += msgpack.packb(record)
            records.append(str(record))
        mock_stdout = io.StringIO()
        fluentd_logging_helpers.overflow_handler_print(pending_records, mock_stdout)

        mock_stdout.seek(0)
        for line_no, line in enumerate(mock_stdout.readlines()):
            self.assertEqual(line.strip(), records[line_no])


if __name__ == '__main__':
    unittest.main()

from __future__ import annotations

import logging
import unittest

from config import logging_config


class TestLoggingConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._root = logging.getLogger()
        self._old_handlers = list(self._root.handlers)
        self._old_level = self._root.level
        self._old_configured = logging_config._CONFIGURED
        logging_config._CONFIGURED = False

    def tearDown(self) -> None:
        self._root.handlers.clear()
        for handler in self._old_handlers:
            self._root.addHandler(handler)
        self._root.setLevel(self._old_level)
        logging_config._CONFIGURED = self._old_configured
        logging_config.clear_correlation_id()

    def test_setup_logging_registers_filter(self) -> None:
        logging_config.setup_logging(level="INFO")
        handlers = self._root.handlers
        self.assertEqual(len(handlers), 1)
        handler_filters = handlers[0].filters
        self.assertTrue(
            any(isinstance(item, logging_config.CorrelationIdFilter) for item in handler_filters)
        )

    def test_setup_logging_is_idempotent(self) -> None:
        logging_config.setup_logging(level="INFO")
        first_handlers = list(self._root.handlers)
        logging_config.setup_logging(level="DEBUG")
        self.assertEqual(self._root.handlers, first_handlers)

    def test_correlation_id_filter_sets_record(self) -> None:
        logging_config.setup_logging(level="INFO")
        logging_config.set_correlation_id("test-correlation")

        handler = self._root.handlers[0]
        record = logging.LogRecord(
            name="tests.logging",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        for filter_item in handler.filters:
            filter_item.filter(record)

        self.assertEqual(record.correlation_id, "test-correlation")

    def test_new_correlation_id_changes_value(self) -> None:
        logging_config.setup_logging(level="INFO")
        logging_config.set_correlation_id("stable")
        new_value = logging_config.new_correlation_id()
        self.assertNotEqual(new_value, "stable")
        self.assertEqual(len(new_value), 32)

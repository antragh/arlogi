"""Test to verify relative path functionality in logger output."""

from arlogi import get_logger, setup_logging


def test_relative_path_logging():
    setup_logging(level="INFO", show_time=False, show_level=True, show_path=True)
    logger = get_logger("test_rel_path")
    logger.info("This message should show with relative path")
    logger.error("Error message with relative path")

    def nested_function():
        logger.info("Message from nested function")

    nested_function()

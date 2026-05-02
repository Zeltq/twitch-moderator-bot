import logging
import unittest
from pathlib import Path

from twitch_moderator.logging_config import configure_logging, DEFAULT_LOG_FILE_PATH


class LoggingConfigTests(unittest.TestCase):
    def test_configure_logging_writes_to_file(self) -> None:
        log_path = Path("tests/.tmp_logs/test.log")
        try:
            configure_logging(log_file_path=log_path)
            logger = logging.getLogger("test_logging_config")
            logger.info("hello log file")

            for handler in logging.getLogger().handlers:
                handler.flush()

            logging.shutdown()

            self.assertTrue(log_path.exists())
            self.assertIn("hello log file", log_path.read_text(encoding="utf-8"))
        finally:
            root_logger = logging.getLogger()
            for handler in list(root_logger.handlers):
                root_logger.removeHandler(handler)
                handler.close()

            if log_path.exists():
                log_path.unlink()
            if log_path.parent.exists():
                log_path.parent.rmdir()

            configure_logging(log_file_path=DEFAULT_LOG_FILE_PATH)


if __name__ == "__main__":
    unittest.main()

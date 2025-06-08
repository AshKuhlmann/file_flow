import logging
import logging.handlers
import pathlib
import sys
from rich.logging import RichHandler

LOG_DIR = pathlib.Path.home() / ".file-sorter"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "file_sorter.log"

def setup_logging(console_level: int = logging.INFO, file_level: int = logging.DEBUG):
    """Configure logging for the entire application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(min(console_level, file_level))

    console_handler = RichHandler(
        level=console_level,
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
    )

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root_logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception

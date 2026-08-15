import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)

from shared.logging.logger import configure_logger, get_logger


configure_logger(
    service_name="test_service",
    log_level="INFO"
)

logger = get_logger(__name__)

logger.info("This is an info log message.")
logger.error("This is an error log message.")
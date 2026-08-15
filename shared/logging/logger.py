import logging
import sys
from datetime import datetime, timezone
from typing import Any

from pythonjsonlogger import jsonlogger


class UTCFJsonFormatter(jsonlogger.JsonFormatter):

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:

        super().add_fields(log_record, record, message_dict)

        log_record["timestamp"] = datetime.now(
            timezone.utc
        ).isoformat()

        log_record["level"] = record.levelname
        log_record["message"] = record.getMessage()


class ServiceNameFilter(logging.Filter):

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.service_name = self.service_name
        return True


def configure_logger(
    service_name: str,
    log_level: str = "INFO",
) -> None:

    formatter = UTCFJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    handler.addFilter(ServiceNameFilter(service_name))

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
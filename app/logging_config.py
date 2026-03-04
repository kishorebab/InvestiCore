import logging
from .config import settings


def configure_logging() -> None:
    level = settings.log_level.upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] [%(correlation_id)s] %(message)s",
    )


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


logging.getLogger().addFilter(CorrelationIdFilter())
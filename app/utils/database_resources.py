import logging
from typing import Any


def close_database_resources(
    database: Any = None,
    cursor: Any = None,
    logger: logging.Logger | None = None,
) -> None:
    """Close database resources independently without masking the main response."""

    log = logger or logging.getLogger(__name__)

    if cursor is not None:
        try:
            cursor.close()
        except Exception:
            log.exception("Failed to close database cursor")

    if database is not None:
        try:
            database.close()
        except Exception:
            log.exception("Failed to close database connection")

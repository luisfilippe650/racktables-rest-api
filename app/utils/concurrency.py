import hashlib
import logging
from typing import Iterable

logger = logging.getLogger(__name__)

LOCK_TIMEOUT_SECONDS = 10
LOCK_PREFIX = "rtapi"


def build_lock_name(namespace: str, *parts) -> str:
    normalized = ":".join(str(part).strip().lower() for part in parts if part is not None)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:40]
    return f"{LOCK_PREFIX}:{namespace}:{digest}"


def acquire_named_locks(cursor, lock_names: Iterable[str], timeout: int = LOCK_TIMEOUT_SECONDS):
    acquired = []

    for lock_name in sorted(set(lock_names)):
        cursor.execute("SELECT GET_LOCK(%s, %s) AS lock_acquired", (lock_name, timeout))
        row = cursor.fetchone()
        lock_acquired = row.get("lock_acquired") if isinstance(row, dict) else row[0]

        if lock_acquired != 1:
            release_named_locks(cursor, acquired)
            return False, lock_name

        acquired.append(lock_name)

    return True, None


def release_named_locks(cursor, lock_names: Iterable[str]):
    for lock_name in reversed(list(dict.fromkeys(lock_names))):
        try:
            cursor.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
        except Exception:
            logger.exception("Failed to release MySQL advisory lock '%s'", lock_name)

import os
import logging
from threading import Lock
from dotenv import load_dotenv
from mysql.connector import Error, pooling

from app.utils.database_resources import close_database_resources

load_dotenv()

logger = logging.getLogger(__name__)

# Global variable to hold the pool instance
_connection_pool = None
_pool_lock = Lock()


def _get_required_db_config():
    config = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "port": os.getenv("DB_PORT"),
    }
    missing = [key for key, value in config.items() if value in (None, "")]
    if missing:
        logger.error("Database configuration is missing required values: %s", ", ".join(missing))
        return None

    try:
        config["port"] = int(config["port"])
        config["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
        config["connection_timeout"] = int(os.getenv("DB_CONNECTION_TIMEOUT", "5"))
        config["read_timeout"] = int(os.getenv("DB_READ_TIMEOUT", "15"))
        config["write_timeout"] = int(os.getenv("DB_WRITE_TIMEOUT", "15"))
    except ValueError:
        logger.exception("Database port, pool size, or timeout is not a valid integer")
        return None

    positive_fields = ("port", "pool_size", "connection_timeout", "read_timeout", "write_timeout")
    invalid = [field for field in positive_fields if config[field] <= 0]
    if invalid:
        logger.error("Database settings must be greater than zero: %s", ", ".join(invalid))
        return None

    return config


def initialize_pool():
    """
    Initialize the connection pool once, safely across concurrent threads.
    """
    global _connection_pool

    if _connection_pool is not None:
        return _connection_pool

    with _pool_lock:
        if _connection_pool is not None:
            return _connection_pool

        config = _get_required_db_config()
        if config is None:
            return None
        try:
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="racktables_pool",
                pool_size=config["pool_size"],
                pool_reset_session=True, # Resets session state when connection returns to pool
                host=config["host"],
                user=config["user"],
                password=config["password"],
                database=config["database"],
                port=config["port"],
                connection_timeout=config["connection_timeout"],
                read_timeout=config["read_timeout"],
                write_timeout=config["write_timeout"],
            )
        except Error as error:
            logger.exception("Failed to create the database connection pool")
            return None

    return _connection_pool


def get_pool():
    """Return the initialized pool, with a thread-safe fallback for direct use."""
    return initialize_pool()

def connect():
    """
    Retrieves a connection from the pool.
    If the pool is not initialized, it tries to initialize it.
    """
    try:
        pool = get_pool()
        if pool:
            connection = pool.get_connection()
            if connection.is_connected():
                return connection
            close_database_resources(database=connection, logger=logger)
        return None

    except Error as error:
        logger.exception("Failed to get a database connection from the pool")
        return None


def connect_with_cursor(dictionary: bool = True):
    """Acquire a pooled connection and cursor as one safely managed operation."""

    database = connect()
    if not database:
        return None, None

    try:
        cursor = database.cursor(dictionary=dictionary)
        return database, cursor
    except Exception:
        logger.exception("Failed to create a database cursor")
        close_database_resources(database=database, logger=logger)
        return None, None

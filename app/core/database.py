import os
import logging
from dotenv import load_dotenv
from mysql.connector import Error, pooling

load_dotenv()

logger = logging.getLogger(__name__)

# Global variable to hold the pool instance
_connection_pool = None


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
    except ValueError:
        logger.exception("Database port or pool size is not a valid integer")
        return None

    return config

def get_pool():
    """
    Initializes and returns the connection pool.
    Uses a singleton pattern to ensure only one pool exists.
    """
    global _connection_pool
    if _connection_pool is None:
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
                port=config["port"]
            )
        except Error as error:
            logger.exception("Failed to create the database connection pool")
            return None
    return _connection_pool

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
        return None

    except Error as error:
        logger.exception("Failed to get a database connection from the pool")
        return None

import os
from dotenv import load_dotenv
from mysql.connector import Error, pooling
import mysql.connector

load_dotenv()

# Global variable to hold the pool instance
_connection_pool = None

def get_pool():
    """
    Initializes and returns the connection pool.
    Uses a singleton pattern to ensure only one pool exists.
    """
    global _connection_pool
    if _connection_pool is None:
        try:
            # Pool configuration
            # pool_name: identifier for the pool
            # pool_size: number of pre-opened connections (default is 5)
            _connection_pool = pooling.MySQLConnectionPool(
                pool_name="racktables_pool",
                pool_size=10, 
                pool_reset_session=True, # Resets session state when connection returns to pool
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                port=os.getenv("DB_PORT")
            )
        except Error as error:
            print("Critical error: failed to create the connection pool ", error)
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
        print("Internal server error: failed to get a connection from the pool ", error)
        return None

def database_user():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("USER_DB_HOST"),
            user=os.getenv("USER_DB_USER"),
            password=os.getenv("USER_DB_PASSWORD"),
            database=os.getenv("USER_DB_NAME"),
            port=os.getenv("USER_DB_PORT")
        )
        if connection.is_connected():
            return connection

    except Error as error:
        print("Internal server error: failed to get a user ", error)
        return None


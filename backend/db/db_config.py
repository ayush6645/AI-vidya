from flask_mysqldb import MySQL
from MySQLdb import Error
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create MySQL instance
mysql = MySQL()

def get_connection():
    """
    Get a MySQL database connection.
    Returns connection object or None if connection fails.
    """
    try:
        conn = mysql.connection
        if conn is None:
            logger.error("MySQL connection is None - check:")
            logger.error("1. mysql.init_app() was called")
            logger.error("2. Database credentials are correct")
            logger.error("3. MySQL server is running")
            return None
            
        # Test connection
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
        logger.debug("Database connection successful")
        return conn
        
    except Error as e:
        logger.error(f"MySQL Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
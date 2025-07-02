import os

class Config:
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public', 'uploads')))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', '[%(asctime)s] %(levelname)s %(name)s: %(message)s')

    # --- Database Configuration ---
    # Fallback database type: 'mysql' or 'sqlite'
    DATABASE_TYPE_FALLBACK = 'sqlite'

    # MySQL default configuration
    MYSQL_CONFIG_FALLBACK = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'chess_ai',
        'pool_size': 10,
        'max_overflow': 20
    }

    # SQLite default configuration
    SQLITE_CONFIG_FALLBACK = {
        'path': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')),
        'pool_size': 5,
        'max_overflow': 10
    } 
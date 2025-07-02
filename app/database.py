import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from app.config import Config
from app.logging_config import logger
from contextlib import contextmanager

# Load environment variables from .env file.
# If .env file is not found, it will not raise an error.
load_dotenv()

# --- Database Configuration ---
# The application supports multiple database backends (MySQL, SQLite, etc.)
# through SQLAlchemy's connection string format.
#
# Examples:
#   - MySQL: mysql+pymysql://user:password@host:port/dbname
#   - SQLite: sqlite:///path/to/database.db
#
# It will prioritize settings from the .env file, falling back to app/config.py.

# --- Database Initialization ---
engine = None
SessionLocal = None
Base = declarative_base()
DB_ENABLED = os.getenv('DB_ENABLED', 'true').lower() == 'true'

if DB_ENABLED:
    # Determine which database to use, prioritizing .env over config.py
    db_type = os.getenv('DB_TYPE', Config.DATABASE_TYPE_FALLBACK).lower()
    logger.info(f"Database type selected: {db_type}")

    db_url = None
    pool_config = {}
    connect_args = {}

    try:
        if db_type == 'mysql':
            cfg = Config.MYSQL_CONFIG_FALLBACK
            host = os.getenv('DB_HOST', cfg['host'])
            port = int(os.getenv('DB_PORT', cfg['port']))
            user = os.getenv('DB_USER', cfg['user'])
            password = os.getenv('DB_PASSWORD', cfg['password'])
            dbname = os.getenv('DB_NAME', cfg['database'])
            
            db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
            
            pool_config['pool_size'] = int(os.getenv('DB_POOL_SIZE', cfg['pool_size']))
            pool_config['max_overflow'] = int(os.getenv('DB_MAX_OVERFLOW', cfg['max_overflow']))

        elif db_type == 'sqlite':
            cfg = Config.SQLITE_CONFIG_FALLBACK
            db_path = os.getenv('DB_PATH', cfg['path'])
            db_url = f"sqlite:///{db_path}"

            pool_config['pool_size'] = int(os.getenv('DB_POOL_SIZE', cfg['pool_size']))
            pool_config['max_overflow'] = int(os.getenv('DB_MAX_OVERFLOW', cfg['max_overflow']))
            connect_args["check_same_thread"] = False
        
        else:
            raise ValueError(f"Unsupported DB_TYPE: {db_type}")

        engine = create_engine(
            db_url,
            pool_size=pool_config.get('pool_size', 5),
            max_overflow=pool_config.get('max_overflow', 10),
            pool_recycle=3600,
            echo=False,
            future=True,
            connect_args=connect_args
        )
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        logger.info(f"Database engine created successfully for '{db_type}'.")

    except (ValueError, Exception) as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        engine = None
        SessionLocal = None
        DB_ENABLED = False

@contextmanager
def get_db_session():
    """
    获取数据库会话的上下文管理器
    
    Usage:
        with get_db_session() as session:
            # 使用session进行数据库操作
            result = session.execute(query)
            session.commit()
    """
    if not DB_ENABLED or SessionLocal is None:
        raise RuntimeError("Database is not enabled or not properly initialized")
    
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def get_db():
    """
    获取数据库会话（用于依赖注入）
    
    Returns:
        Session: SQLAlchemy session
    """
    if not DB_ENABLED or SessionLocal is None:
        raise RuntimeError("Database is not enabled or not properly initialized")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
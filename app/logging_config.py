"""
日志配置模块
"""
import logging
from logging.handlers import RotatingFileHandler
import os
import sys; print('PYTHONPATH:', sys.path)
import app.routes
from app.config import Config
import logging.config
from app.shutdown import shutdown_manager

# 确保日志目录存在
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志配置字典
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': os.path.join(LOG_DIR, 'recognition.log'),
            'maxBytes': 2*1024*1024,  # 2MB
            'backupCount': 5,
            'encoding': 'utf8',
            'delay': True  # 延迟创建文件，直到第一次写入
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': 2*1024*1024,  # 2MB
            'backupCount': 5,
            'encoding': 'utf8',
            'delay': True  # 延迟创建文件，直到第一次写入
        }
    },
    'loggers': {
        'app.services.recognition': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'app.engine': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'error_file']
    }
}

def cleanup_logging():
    """
    清理所有日志处理器
    """
    for handler in logging.getLogger().handlers[:]:
        try:
            handler.close()
            logging.getLogger().removeHandler(handler)
        except:
            pass
        
    for name in logging.root.manager.loggerDict.keys():
        logger = logging.getLogger(name)
        for handler in logger.handlers[:]:
            try:
                handler.close()
                logger.removeHandler(handler)
            except:
                pass

def setup_logging():
    """
    设置日志配置
    """
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 注册为最后一个清理函数（优先级最低）
    shutdown_manager.register(cleanup_logging, priority=-100)

# 初始化日志配置
setup_logging()

# 创建主日志记录器
logger = logging.getLogger('chess-helper') 
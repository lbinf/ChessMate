"""
配置管理 - 用于跨项目迁移
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载.env文件（如果存在）
load_dotenv()

class Config:
    """配置管理类"""
    
    # Redis配置
    REDIS_CONFIG = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD', '123456')
    }
    
    # 队列配置
    QUEUE_CONFIG = {
        'chess_message_queue': 'chess_message_queue',
    }
    
    # 日志配置
    LOG_CONFIG = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': os.getenv('LOG_FILE', 'logs/chess_consumer.log')
    }
    
    # 消费者配置
    CONSUMER_CONFIG = {
        'batch_size': int(os.getenv('CONSUMER_BATCH_SIZE', 10)),
        'timeout': int(os.getenv('CONSUMER_TIMEOUT', 1)),
        'retry_count': int(os.getenv('CONSUMER_RETRY_COUNT', 3)),
        'retry_delay': int(os.getenv('CONSUMER_RETRY_DELAY', 1))
    }
    
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """获取Redis配置"""
        return cls.REDIS_CONFIG.copy()
    
    @classmethod
    def get_queue_config(cls) -> Dict[str, Any]:
        """获取队列配置"""
        return cls.QUEUE_CONFIG.copy()
    
    @classmethod
    def get_log_config(cls) -> Dict[str, Any]:
        """获取日志配置"""
        return cls.LOG_CONFIG.copy()
    
    @classmethod
    def get_consumer_config(cls) -> Dict[str, Any]:
        """获取消费者配置"""
        return cls.CONSUMER_CONFIG.copy()
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置"""
        try:
            # 验证Redis配置
            redis_config = cls.get_redis_config()
            required_redis_fields = ['host', 'port', 'db', 'password']
            for field in required_redis_fields:
                if field not in redis_config:
                    print(f"❌ Redis配置缺少字段: {field}")
                    return False
            
            # 验证队列配置
            queue_config = cls.get_queue_config()
            if not queue_config.get('chess_message_queue'):
                print("❌ 队列配置缺少chess_message_queue")
                return False
            
            print("✅ 配置验证通过")
            return True
            
        except Exception as e:
            print(f"❌ 配置验证失败: {str(e)}")
            return False

# 环境变量示例
ENV_EXAMPLE = """
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=123456

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/chess_consumer.log

# 消费者配置
CONSUMER_BATCH_SIZE=10
CONSUMER_TIMEOUT=1
CONSUMER_RETRY_COUNT=3
CONSUMER_RETRY_DELAY=1
""" 
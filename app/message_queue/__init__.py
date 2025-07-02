"""
象棋消息处理迁移包
用于将消息分发、配置、消费功能迁移到其他项目
"""

from .chess_message_models import GameMessage,ChessMessage, MessageType
from .redis_consumer import RedisConsumer
from .config import Config

__version__ = "1.0.0"
__author__ = "Chess Message Migration"

__all__ = [
    'GameMessage',
    'ChessMessage',
    'MessageType',
    'RedisConsumer',
    'Config'
] 
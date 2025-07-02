"""
象棋消息模型 - 用于跨项目迁移
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class MessageType(Enum):
    """消息类型枚举"""
    MATCH_ACK = "match_ack_msg"
    ENTER_ROUND_ACK = "enterround_ack_msg"
    ADD_GAME_PLAYER_INFO_ACK = "addgameplayerinfo_ack_msg"
    CHESS_MOVE_ACK = "chessmove_ack_msg"
    CHESS_GAME_OVER_ACK = "chessgameover_ack_msg"
    CHESS_SURRENDER_ACK = "chesssurrender_ack_msg"
    CHESS_RESPOND_RESULT_EX_ACK = "chessrespondresultex_ack_msg"
    CHESS_PROTOCOL_ACK = "chessprotocol_ack_msg"

@dataclass
class GameMessage:
    """游戏消息基类"""
    message_type: str
    data: Dict[str, Any]
    timestamp: str
    source: str
    priority: int

@dataclass
class ChessMessage:
    """象棋消息"""
    message_type: MessageType
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    priority: int = 1
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChessMessage':
        """从字典创建消息对象"""
        # 解析消息类型
        message_type_str = data.get('message_type', 'unknown')
        try:
            message_type = MessageType(message_type_str)
        except ValueError:
            message_type = MessageType.UNKNOWN
        
        # 解析时间戳
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()

        return cls(
            message_type=message_type,
            data=data.get('data', {}),
            timestamp=timestamp,
            source=data.get('source', 'unknown'),
            priority=data.get('priority', 1)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'message_type': self.message_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'priority': self.priority
        }
        return result
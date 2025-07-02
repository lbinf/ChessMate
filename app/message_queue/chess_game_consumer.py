import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os

from app.chess.game_manager import game_manager, Player, GameResult, GameStatus
from app.database import get_db_session
from sqlalchemy import text
from app.services.analysis import analyze_fen
from .chess_message_models import MessageType,ChessMessage,GameMessage

logger = logging.getLogger(__name__)

class ChessGameMessageProcessor:
    """象棋游戏消息处理器"""
    
    def __init__(self):
        self.active_games: Dict[str, Dict[str, Any]] = {}
        self.user_games: Dict[int, str] = {}  # user_id -> game_id 映射
        self._msg_count = 0
        self.current_user_id = None # 用于判断AI应该为哪一方服务
        
    def process_message(self, message_data: Any) -> Dict[str, Any]:
        # 记录最原始的消息用于调试
        logger.debug(f"收到原始消息: {json.dumps(message_data, ensure_ascii=False)}")
        
        # 自动解包被`message`键包裹的消息
        if isinstance(message_data, dict) and 'message' in message_data and isinstance(message_data['message'], dict):
            logger.info("检测到消息被包裹，自动解包...")
            message_data = message_data['message']

        # 自动兼容ChessMessage对象
        if not isinstance(message_data, dict):
            if hasattr(message_data, 'to_dict'):
                message_data = message_data.to_dict()
            elif hasattr(message_data, '__dict__'):
                message_data = dict(message_data.__dict__)
            else:
                logger.error(f"不支持的消息类型: {type(message_data)}，原始内容: {message_data}")
                return {"success": False, "error": f"不支持的消息类型: {type(message_data)}", "raw": str(message_data)}
        
        self._msg_count += 1
        
        result = {}
        try:
            message = GameMessage(
                message_type=message_data.get("message_type"),
                data=message_data.get("data", {}),
                timestamp=message_data.get("timestamp"),
                source=message_data.get("source"),
                priority=message_data.get("priority", 1)
            )
            logger.info(f"处理消息: {message.message_type}")
            
            # 根据消息类型路由到不同的处理器
            if message.message_type == MessageType.CHESS_PROTOCOL_ACK.value:
                result = self._handle_chess_protocol(message)
            elif message.message_type == MessageType.CHESS_MOVE_ACK.value:
                result = self._handle_chess_move(message)
            elif message.message_type == MessageType.CHESS_GAME_OVER_ACK.value:
                result = self._handle_chess_game_over(message)
            elif message.message_type == MessageType.CHESS_RESPOND_RESULT_EX_ACK.value:
                result = self._handle_chess_respond_result(message)
            else:
                logger.warning(f"未知消息类型: {message.message_type}, 原始消息: {json.dumps(message_data, ensure_ascii=False)}")
                result = {"success": False, "error": f"未知消息类型: {message.message_type}"}
            
            # 确保返回结果中包含消息类型
            if 'message_type' not in result:
                result['message_type'] = message.message_type
            return result
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            serializable_message = message_data
            if not isinstance(message_data, dict):
                if hasattr(message_data, 'to_dict'):
                    serializable_message = message_data.to_dict()
                elif hasattr(message_data, '__dict__'):
                    serializable_message = dict(message_data.__dict__)
                else:
                    serializable_message = str(message_data)
            return {"success": False, "error": str(e), "raw": message_data, "message_type": message_data.get("message_type")}
    
    def _handle_chess_protocol(self, message: GameMessage) -> Dict[str, Any]:
        """处理游戏开始协议消息 (chessprotocol_ack_msg)"""
        try:
            game_data = message.data.get("game", {})
            event_data = message.data.get("data", {})
            
            game_id = game_data.get("gameid")
            if not game_id:
                return {"success": False, "error": "缺少 gameid"}

            current_user_id = game_data.get("current_userid")
            current_user_start = game_data.get("current_user_start")

            players_map = event_data.get("players", {})
            red_info = players_map.get("0", {}) # seat 0 is red
            black_info = players_map.get("1", {}) # seat 1 is black
            logger.info(f"red_info: {red_info}")
            logger.info(f"black_info: {black_info}")

            if not red_info or not black_info:
                return {"success": False, "error": "缺少玩家信息"}

            red_player = Player(
                user_id=red_info.get("userid"),
                username=red_info.get("nickname"),
                extra_info={"figureid": red_info.get("figureid")}
            )
            black_player = Player(
                user_id=black_info.get("userid"),
                username=black_info.get("nickname"),
                extra_info={"figureid": black_info.get("figureid")}
            )

            extra_info = {
                "game": game_data,
                "players": players_map,
                "match_info": event_data.get("match_info",{}),
                "protocol_info": event_data.get("protocol_info",{}),
                "source": message.source
            }
            # 使用game_manager创建并持久化游戏
            game_manager.create_game(
                game_id=game_id,
                red_player=red_player,
                black_player=black_player,
                match_id=game_data.get("matchid"),
                current_user_id=current_user_id,
                current_user_start=current_user_start,
                extra_info=extra_info
            )

            game = game_manager.get_game(game_id)
            if not game:
                return {"success": False, "error": f"游戏创建后无法在管理器中找到: {game_id}"}
                
            game.start_game()
            logger.info(f"游戏协议处理成功，游戏实例创建并开始: {game_id}")
            # 我方，则让ai推荐走法
            if current_user_start:
                logger.info(f"我方先手(uid={current_user_id})走棋，请求AI分析...")
                fen = game.board.to_fen()
                logger.info(f"fen:{fen}")
                is_red_turn = game.board.player_to_move == 'red'
                board_array = game.board.fen_to_board_array(fen)  # 获取二维数组棋盘

                ai_move = analyze_fen(fen, is_red_turn, board_array)
                logger.info(f"AI推荐走法 for {game_id}: {ai_move}")
                move = ai_move.get('move','')
                if not move:
                    game.board.handle_ucci_move(move)

            return {"success": True, "game_id": game_id, "status": "game_created_and_started"}

        except Exception as e:
            logger.error(f"处理游戏开始协议失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _handle_chess_move(self, message: GameMessage) -> Dict[str, Any]:
        """处理走棋消息, 并调用AI分析"""
        try:
            game_data = message.data.get("game", {})
            move_data = message.data.get("data", {})
            
            game_id = game_data.get("gameid")
            if not game_id:
                return {"success": False, "error": "缺少游戏ID"}

            chess_game = game_manager.get_game(game_id)
            if not chess_game:
                logger.warning(f"处理走棋消息时，游戏实例不存在, game_id: {game_id}")
                return {"success": False, "error": f"游戏实例不存在: {game_id}"}

            # 解析移动数据
            from_pos = (move_data.get("beginposx"), move_data.get("beginposy"))
            to_pos = (move_data.get("endposx"), move_data.get("endposy"))
            
            if not from_pos or not to_pos:
                return {"success": False, "error": "缺少移动坐标"}
            
            # 在game_manager中执行移动并持久化
            move_result = game_manager.make_move(game_id, from_pos, to_pos)
            if not move_result.get("success"):
                return move_result # 如果移动失败，直接返回结果

            logger.info(f"执行移动成功: {game_id}, {move_result.get('notation')}")

            # AI分析与推荐
            # 判断是否需要AI提供建议（轮到我方走棋）
            is_ai_move = False
            my_user_id = chess_game.current_user_id # 使用当前棋局的user_id
            logger.info(f"my_user_id: {my_user_id},{chess_game.current_user_start}")
            if chess_game.current_user_start:
                if chess_game.board.player_to_move == 'red':
                    is_ai_move = True
            else:
                if chess_game.board.player_to_move == 'black':
                    is_ai_move = True
            logger.info(f"red_user_id{chess_game.red_player.user_id},move:{chess_game.board.player_to_move},{is_ai_move}")
            logger.info(f"black_user_id:{chess_game.black_player.user_id},move:{chess_game.board.player_to_move},{is_ai_move}")
            ai_move = None
            if is_ai_move:
                logger.info(f"轮到我方(uid={my_user_id})走棋，请求AI分析...")
                fen = move_result.get('fen')
                logger.info(f"fen:{fen}")
                is_red_turn = chess_game.board.player_to_move == 'red'
                board_array = chess_game.board.fen_to_board_array(fen) # 获取二维数组棋盘
                
                ai_move = analyze_fen(fen, is_red_turn, board_array)
                logger.info(f"AI推荐走法 for {game_id}: {ai_move}")

            move_result['ai_recommendation'] = ai_move
            return move_result
            
        except Exception as e:
            logger.error(f"处理走棋消息失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _handle_chess_game_over(self, message: GameMessage) -> Dict[str, Any]:
        """处理游戏结束消息，仅做标记，不判定胜负"""
        try:
            game_data = message.data.get("game", {})
            data = message.data.get("data", {})
            
            game_id = game_data.get("gameid")
            end_reason = data.get("text", "unknown") # 结束原因
            
            if not game_id:
                return {"success": False, "error": "缺少游戏ID"}
            
            chess_game = game_manager.get_game(game_id)
            if not chess_game:
                logger.warning(f"处理游戏结束消息时，游戏实例不存在, game_id: {game_id}")
                return {"success": False, "error": f"游戏实例不存在: {game_id}"}
            
            # 标记游戏结束，但不判定胜负
            chess_game.status = GameStatus.FINISHED
            chess_game.end_time = datetime.now()
            # 可选：记录结束原因
            chess_game.extra_info['end_reason'] = end_reason
            chess_game._update_game_in_database()
            
            logger.info(f"游戏结束: {game_id}, 原因: {end_reason}")
            
            return {
                "success": True,
                "game_id": game_id,
                "end_reason": end_reason,
                "status": "finished"
            }
        except Exception as e:
            logger.error(f"处理游戏结束消息失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _handle_chess_respond_result(self, message: GameMessage) -> Dict[str, Any]:
        """处理游戏结果确认消息，判定胜负并写入数据库"""
        try:
            game_data = message.data.get("game", {})
            data = message.data.get("data", {})
            
            game_id = game_data.get("gameid")
            loss_seat = data.get("lossseat") # 0=红方输，1=黑方输
            
            if not game_id:
                return {"success": False, "error": "缺少游戏ID"}
            if loss_seat not in (0, 1):
                return {"success": False, "error": "lossseat 字段无效"}
            
            chess_game = game_manager.get_game(game_id)
            if not chess_game:
                logger.warning(f"处理游戏结果响应消息时，游戏实例不存在, game_id: {game_id}")
                return {"success": False, "error": f"游戏实例不存在: {game_id}"}
            
            # 判定胜负
            if loss_seat == 0:
                result = GameResult.BLACK_WIN
            else:
                result = GameResult.RED_WIN
            
            chess_game.end_game(result)
            chess_game._update_game_in_database()
            
            logger.info(f"游戏结果确认: {game_id}, 失败方: {loss_seat}, 结果: {result.value}")
            
            return {
                "success": True,
                "game_id": game_id,
                "result": result.value,
                "loser_seat": loss_seat,
                "status": "finished"
            }
        except Exception as e:
            logger.error(f"处理游戏结果消息失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _create_chess_game_instance(self, game_id: str, players_info: Dict[str, Any]):
        """创建游戏管理器中的游戏实例"""
        try:
            # 解析玩家信息
            red_player_info = players_info.get("red", {})
            black_player_info = players_info.get("black", {})
            
            # 创建玩家对象
            red_player = Player(
                user_id=red_player_info.get("user_id", 0),
                username=red_player_info.get("username", "红方"),
                rating=red_player_info.get("rating"),
                extra_info=red_player_info.get("extra_info")
            )
            
            black_player = Player(
                user_id=black_player_info.get("user_id", 0),
                username=black_player_info.get("username", "黑方"),
                rating=black_player_info.get("rating"),
                extra_info=black_player_info.get("extra_info")
            )
            
            # 获取游戏信息
            game_info = self.active_games.get(game_id, {})
            
            # 创建游戏实例，使用原始游戏ID
            chess_game = game_manager.create_game(
                red_player=red_player,
                black_player=black_player,
                match_id=game_info.get("match_id"),
                extra_info=game_info.get("ext_info"),
                game_id=game_id  # 指定游戏ID
            )
            
            # 开始游戏
            if chess_game:  # 确保创建成功
                game_instance = game_manager.get_game(game_id)
                if game_instance:
                    game_instance.start_game()
                    logger.info(f"开始游戏: {game_id}")
                else:
                    logger.error(f"无法获取游戏实例: {game_id}")
            else:
                logger.error(f"创建游戏实例失败: {game_id}")
            
        except Exception as e:
            logger.error(f"创建游戏实例失败: {e}")
    
    def get_game_status(self, game_id: str) -> Optional[Dict[str, Any]]:
        """获取游戏状态"""
        return self.active_games.get(game_id)
    
    def get_user_game(self, user_id: int) -> Optional[str]:
        """获取用户的游戏ID"""
        return self.user_games.get(user_id)
    
    def list_active_games(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃游戏"""
        return self.active_games.copy()

    def get_statistics(self):
        """返回简单的消息统计信息"""
        return {
            "total_messages": self._msg_count,
            "active_games": len(self.active_games),
            "user_games": len(self.user_games)
        }


# 全局消息处理器实例
chess_message_processor = ChessGameMessageProcessor() 
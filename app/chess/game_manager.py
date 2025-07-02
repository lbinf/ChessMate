import uuid
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .board import ChessBoard, ChessPiece
from app.database import get_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class GameStatus(Enum):
    """游戏状态枚举"""
    WAITING = "waiting"      # 等待开始
    PLAYING = "playing"      # 进行中
    FINISHED = "finished"    # 已结束
    PAUSED = "paused"       # 暂停

class GameResult(Enum):
    """游戏结果枚举"""
    RED_WIN = "红胜"
    BLACK_WIN = "黑胜"
    DRAW = "和棋"
    UNKNOWN = "未知"

@dataclass
class Player:
    """玩家信息"""
    user_id: int
    username: str
    rating: Optional[int] = None
    extra_info: Optional[Dict] = None

@dataclass
class GameMove:
    """游戏移动记录"""
    move_number: int
    side: str  # 'red' or 'black'
    seat: int  # 0 for red, 1 for black
    piece: str
    from_pos: str
    to_pos: str
    move_type: str
    move_time: int
    ctm: str
    cc: str
    fen: str
    fen_side: str

class ChessGameManager:
    """象棋状态管理类"""
    
    def __init__(self):
        self.active_games: Dict[str, 'ChessGame'] = {}
        self.game_history: Dict[str, 'ChessGame'] = {}
        
    def create_game(self, 
                   red_player: Player, 
                   black_player: Player,
                   match_id: Optional[int] = None,
                   current_user_id: Optional[int] = None,
                   current_user_start: Optional[bool] = None,
                   extra_info: Optional[Dict] = None,
                   game_id: Optional[str] = None) -> str:

        """
        创建新游戏
        
        Args:
            red_player: 红方玩家
            black_player: 黑方玩家
            match_id: 对局ID
            current_user_id: 当前用户ID
            current_user_start: 当前用户是否先手
            extra_info: 额外信息
            game_id: 指定游戏ID（可选）
            
        Returns:
            str: 游戏ID
        """
        # 生成游戏ID
        if game_id is None:
            game_id = self._generate_game_id()
        
        # 检查游戏ID是否已存在
        if game_id in self.active_games or game_id in self.game_history:
            logger.warning(f"游戏ID已存在: {game_id}")
            return game_id
        
        # 创建游戏实例
        game = ChessGame(
            game_id=game_id,
            red_player=red_player,
            black_player=black_player,
            match_id=match_id,
            current_user_id=current_user_id,
            current_user_start=current_user_start,
            extra_info=extra_info
        )
        logger.info(f"red_play: {red_player} black_player: {black_player}")
        # 保存到数据库
        game.save_to_database()
        
        # 添加到活跃游戏列表
        self.active_games[game_id] = game
        
        logger.info(f"创建新游戏: {game_id}, 红方: {red_player.username}, 黑方: {black_player.username}")
        
        return game_id
    
    def get_game(self, game_id: str) -> Optional['ChessGame']:
        """获取游戏实例"""
        return self.active_games.get(game_id) or self.game_history.get(game_id)
    
    def make_move(self, game_id: str, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Dict:
        """
        执行移动
        
        Args:
            game_id: 游戏ID
            from_pos: 起始位置
            to_pos: 目标位置
            
        Returns:
            Dict: 移动结果信息
        """
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"游戏不存在: {game_id}")
        
        if game.status != GameStatus.PLAYING:
            raise ValueError(f"游戏状态不允许移动: {game.status.value}")
        
        # 执行移动
        result = game.make_move(from_pos, to_pos)
        
        # 检查游戏是否结束
        if game.is_game_over():
            game.end_game()
            # 移动到历史记录
            if game_id in self.active_games:
                self.game_history[game_id] = self.active_games.pop(game_id)
        
        return result
    
    def get_game_status(self, game_id: str) -> Dict:
        """获取游戏状态"""
        game = self.get_game(game_id)
        if not game:
            return {"error": "游戏不存在"}
        
        return game.get_status()
    
    def list_active_games(self) -> List[Dict]:
        """获取所有活跃游戏"""
        return [game.get_status() for game in self.active_games.values()]
    
    def list_finished_games(self) -> List[Dict]:
        """获取所有已结束游戏"""
        return [game.get_status() for game in self.game_history.values()]
    
    def _generate_game_id(self) -> str:
        """生成游戏ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}"


class ChessGame:
    """单个象棋游戏类"""
    
    def __init__(self, 
                 game_id: str,
                 red_player: Player,
                 black_player: Player,
                 match_id: Optional[int] = None,
                 current_user_id: Optional[int] = None,
                 current_user_start: Optional[bool] = None,
                 extra_info: Optional[Dict] = None):
        self.game_id = game_id
        self.red_player = red_player
        self.black_player = black_player
        self.match_id = match_id
        self.current_user_id = current_user_id
        self.current_user_start = current_user_start
        self.extra_info = extra_info or {}
        
        # 游戏状态
        self.status = GameStatus.WAITING
        self.start_time = None
        self.end_time = None
        self.result = GameResult.UNKNOWN
        
        # 棋盘和移动记录
        self.board = ChessBoard()
        self.moves: List[GameMove] = []
        self.current_move_number = 0
        
        # 游戏统计
        self.red_time_used = 0
        self.black_time_used = 0
        self.last_move_time = None
        
    def start_game(self) -> Dict:
        """开始游戏"""
        if self.status != GameStatus.WAITING:
            raise ValueError("游戏状态不允许开始")
        
        self.status = GameStatus.PLAYING
        self.start_time = datetime.now()
        self.last_move_time = time.time()
        
        # 更新数据库
        self._update_game_in_database()
        
        logger.info(f"游戏开始: {self.game_id}")
        
        return {
            "game_id": self.game_id,
            "status": "started",
            "start_time": self.start_time.isoformat(),
            "board": str(self.board),
            "fen": self.board.to_fen()
        }
    
    def make_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> Dict:
        """
        执行移动
        
        Args:
            from_pos: 起始位置 (x, y)
            to_pos: 目标位置 (x, y)
            
        Returns:
            Dict: 移动结果
        """
        if self.status != GameStatus.PLAYING:
            raise ValueError("游戏状态不允许移动")
        
        # 检查位置是否有棋子
        if from_pos not in self.board.pieces:
            raise ValueError(f"起始位置 {from_pos} 没有棋子")
        
        piece = self.board.pieces[from_pos]
        
        # 检查是否轮到该玩家
        current_player = 'red' if self.board.player_to_move == 'red' else 'black'
        if piece.color != current_player:
            raise ValueError(f"轮到{current_player}方，但移动的是{piece.color}方棋子")
        
        # 计算移动时间
        current_time = time.time()
        move_time = int((current_time - self.last_move_time) * 1000)  # 毫秒
        self.last_move_time = current_time
        
        # 更新玩家用时
        if piece.color == 'red':
            self.red_time_used += move_time
        else:
            self.black_time_used += move_time
        
        # 修正：必须在棋盘状态改变前判断是否吃子
        is_capture = to_pos in self.board.pieces
        
        # 执行移动
        try:
            notation = self.board.move_piece(from_pos, to_pos)
        except Exception as e:
            raise ValueError(f"移动失败: {e}")
        
        # 优化：在移动后判断是否将军
        move_type = "吃子" if is_capture else "移动"
        if self.board.is_in_check(self.board.player_to_move):
            move_type += "(将军)"
        
        # 记录移动
        self.current_move_number += 1
        move_record = GameMove(
            move_number=self.current_move_number,
            side=piece.color,
            seat=0 if piece.color == 'red' else 1,
            piece=piece.name,
            from_pos=f"{from_pos[0]},{from_pos[1]}",
            to_pos=f"{to_pos[0]},{to_pos[1]}",
            move_type=move_type, # 使用新的移动类型
            move_time=move_time,
            ctm=self.board.coords_to_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1]),
            cc=notation,
            fen=self.board.to_fen(),
            fen_side='w' if self.board.player_to_move == 'red' else 'b'
        )
        
        self.moves.append(move_record)
        
        # 保存到数据库
        self._save_move_to_database(move_record)
        
        # 检查游戏是否结束
        game_over = self.is_game_over()
        if game_over:
            self.end_game() # 如果吃王了，直接结束游戏
        
        return {
            "success": True,
            "game_id": self.game_id,
            "move_number": self.current_move_number,
            "piece": piece.name,
            "from_pos": from_pos,
            "to_pos": to_pos,
            "notation": notation,
            "fen": self.board.to_fen(),
            "board": str(self.board),
            "game_over": game_over,
            "next_player": self.board.player_to_move
        }
    
    def is_game_over(self) -> bool:
        """检查游戏是否结束"""
        # 这里可以添加更复杂的游戏结束检查逻辑
        # 比如将军、绝杀、和棋等
        # 目前简单实现，可以根据需要扩展
        
        # 检查是否有将/帅
        red_king = False
        black_king = False
        
        for piece in self.board.pieces.values():
            if piece.name == '帅' and piece.color == 'red':
                red_king = True
            elif piece.name == '将' and piece.color == 'black':
                black_king = True
        
        return not (red_king and black_king)
    
    def end_game(self, result: Optional[GameResult] = None):
        """结束游戏"""
        self.status = GameStatus.FINISHED
        self.end_time = datetime.now()
        
        if result:
            self.result = result
        elif self.is_game_over():
            # 自动判断胜负
            red_king = any(p.name == '帅' and p.color == 'red' for p in self.board.pieces.values())
            black_king = any(p.name == '将' and p.color == 'black' for p in self.board.pieces.values())
            
            if red_king and not black_king:
                self.result = GameResult.RED_WIN
            elif black_king and not red_king:
                self.result = GameResult.BLACK_WIN
            else:
                self.result = GameResult.DRAW
        
        # 更新数据库
        self._update_game_in_database()
        
        logger.info(f"游戏结束: {self.game_id}, 结果: {self.result.value}")
    
    def get_status(self) -> Dict:
        """获取游戏状态"""
        return {
            "game_id": self.game_id,
            "match_id": self.match_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "red_player": asdict(self.red_player),
            "black_player": asdict(self.black_player),
            "result": self.result.value,
            "current_move_number": self.current_move_number,
            "board": str(self.board),
            "fen": self.board.to_fen(),
            "next_player": self.board.player_to_move,
            "red_time_used": self.red_time_used,
            "black_time_used": self.black_time_used,
            "current_user_id": self.current_user_id,
            "current_user_start": self.current_user_start,
            "extra_info": self.extra_info
        }
    
    def get_moves(self) -> List[Dict]:
        """获取所有移动记录"""
        return [asdict(move) for move in self.moves]
    
    def save_to_database(self):
        """保存游戏到数据库"""
        try:
            with get_db_session() as session:
                # 检查记录是否已存在
                check_sql = "SELECT id FROM ai_chess_game WHERE chess_id = :chess_id"
                existing = session.execute(text(check_sql), {"chess_id": self.game_id}).first()
                if existing:
                    logger.info(f"游戏 {self.game_id} 已存在于数据库中，跳过插入。")
                    return
                
                # 插入游戏记录
                insert_game_sql = """
                INSERT INTO ai_chess_game 
                (chess_id, match_id, start_time, red_user_id, black_user_id, extra_info)
                VALUES (:chess_id, :match_id, :start_time, :red_user_id, :black_user_id, :extra_info)
                """
                
                # 在extra_info中加入current_user信息
                db_extra_info = self.extra_info.copy()
                db_extra_info['current_user_id'] = self.current_user_id
                db_extra_info['current_user_start'] = self.current_user_start

                session.execute(text(insert_game_sql), {
                    "chess_id": self.game_id,
                    "match_id": self.match_id,
                    "start_time": self.start_time,
                    "red_user_id": self.red_player.user_id,
                    "black_user_id": self.black_player.user_id,
                    "extra_info": json.dumps(db_extra_info, ensure_ascii=False)
                })
                
                session.commit()
                logger.info(f"游戏保存到数据库: {self.game_id}")
                
        except Exception as e:
            logger.error(f"保存游戏到数据库失败: {e}")
            raise
    
    def _update_game_in_database(self):
        """更新游戏状态到数据库"""
        try:
            with get_db_session() as session:
                update_sql = """
                UPDATE ai_chess_game 
                SET start_time = :start_time, end_time = :end_time, result = :result, extra_info = :extra_info
                WHERE chess_id = :chess_id
                """
                
                # 在extra_info中加入current_user信息
                db_extra_info = self.extra_info.copy()
                db_extra_info['current_user_id'] = self.current_user_id
                db_extra_info['current_user_start'] = self.current_user_start

                session.execute(text(update_sql), {
                    "start_time": self.start_time,
                    "end_time": self.end_time,
                    "result": self.result.value,
                    "chess_id": self.game_id,
                    "extra_info": json.dumps(db_extra_info, ensure_ascii=False)
                })
                
                session.commit()
                
        except Exception as e:
            logger.error(f"更新游戏状态失败: {e}")
            raise
    
    def _save_move_to_database(self, move: GameMove):
        """保存移动记录到数据库"""
        try:
            with get_db_session() as session:
                insert_move_sql = """
                INSERT INTO ai_chess_move 
                (game_id, move_number, side, seat, piece, from_pos, to_pos, 
                 move_type, move_time, ctm, cc, fen, fen_side, chess_id)
                VALUES 
                ((SELECT id FROM ai_chess_game WHERE chess_id = :chess_id),
                 :move_number, :side, :seat, :piece, :from_pos, :to_pos,
                 :move_type, :move_time, :ctm, :cc, :fen, :fen_side, :chess_id)
                """
                
                session.execute(text(insert_move_sql), {
                    "chess_id": self.game_id,
                    "move_number": move.move_number,
                    "side": move.side,
                    "seat": move.seat,
                    "piece": move.piece,
                    "from_pos": move.from_pos,
                    "to_pos": move.to_pos,
                    "move_type": move.move_type,
                    "move_time": move.move_time,
                    "ctm": move.ctm,
                    "cc": move.cc,
                    "fen": move.fen,
                    "fen_side": move.fen_side
                })
                
                session.commit()
                
        except Exception as e:
            logger.error(f"保存移动记录失败: {e}")
            raise


# 全局游戏管理器实例
game_manager = ChessGameManager() 
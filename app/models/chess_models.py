from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint, text, SmallInteger, BigInteger, JSON, ForeignKey, Index, CHAR
from app.database import Base

class AiChess(Base):
    __tablename__ = 'ai_chess'
    __table_args__ = (
        UniqueConstraint('fen', 'is_move', 'move', name='uq_fen_is_move_move'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    fen = Column(String(128), nullable=False, index=True, comment='棋盘FEN (不包含走棋方)')
    is_move = Column(String(2), nullable=False, server_default='w', comment='哪方走棋, w:红方 b:黑方')
    move = Column('move', String(16), nullable=False, comment='走法 (例如 h2e2)')
    chinese_move = Column('chinese_move', String(16), nullable=False, comment='中文走法 (例如 马二进三)')
    source = Column('source', SmallInteger, nullable=False, server_default=text('0'), comment='分析来源 (0: 本地引擎, 1: 云库)')
    score = Column(Integer, nullable=False, server_default=text('0'), comment='引擎分数')
    rank = Column('rank', Integer, nullable=False, server_default=text('0'), comment='云库中的排名')
    note = Column('note', String(16), nullable=False, server_default='', comment='云库中的注释')
    win_rate = Column(Integer, nullable=False, server_default=text('0'), comment='胜率 (整数, e.g., 5050 for 50.50%)')
    created_at = Column(DateTime, server_default=func.now(), comment='记录创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='记录更新时间')

class AIChessGame(Base):
    __tablename__ = 'ai_chess_game'
    __table_args__ = (
        UniqueConstraint('chess_id', name='uq_chess_id'),
    )
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键，自增ID')
    chess_id = Column(String(64), nullable=False, comment='棋局唯一ID')
    match_id = Column(BigInteger, comment='比赛ID')
    start_time = Column(DateTime, comment='对局开始时间')
    end_time = Column(DateTime, comment='对局结束时间')
    red_user_id = Column(BigInteger, comment='红方用户ID')
    black_user_id = Column(BigInteger, comment='黑方用户ID')
    result = Column(String(16), comment='对局结果（红胜/黑胜/和棋/未知）')
    extra_info = Column(JSON, comment='其他信息（如微信、平台等）')

class AIChessMove(Base):
    __tablename__ = 'ai_chess_move'
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键，自增ID')
    game_id = Column(BigInteger, ForeignKey('ai_chess_game.id'), nullable=False, comment='关联ai_chess_game.id')
    chess_id = Column(String(64), nullable=False, comment='棋局唯一ID')
    move_number = Column(Integer, comment='步数')
    side = Column(String(8), comment='红方/黑方')
    seat = Column(Integer, comment='0红方/1黑方')
    piece = Column(String(8), comment='棋子名称')
    from_pos = Column(String(8), comment='起点坐标')
    to_pos = Column(String(8), comment='终点坐标')
    move_type = Column(String(16), comment='移动/吃子/将军/绝杀等')
    move_time = Column(BigInteger, comment='时间戳')
    ctm = Column(String(8), comment='引擎走法')
    cc = Column(String(16), comment='中文走法')
    fen = Column(String(128), comment='当前局面FEN')
    fen_side = Column(CHAR(1), comment='w红方/b黑方')
    created_at = Column(DateTime, server_default=func.now(), comment='记录创建时间')

    __table_args__ = (
        Index('idx_fen', 'fen'),
        Index('idx_game_move', 'game_id', 'move_number'),
        Index('idx_chess_id', 'chess_id'),
    ) 
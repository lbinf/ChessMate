from app.engine import engine_instance
from app.logging_config import logger
from app.engine.board import convert_move_to_chinese, is_valid_move_format
from app.services.db_service import get_db, add_analysis_to_db
from app.services.cloud_service import get_chessdb_analysis
import re

def _parse_engine_score(lines: list) -> int:
    """Parses the 'score cp' from engine analysis lines."""
    for line in reversed(lines):
        if 'score mate' in line:
            match = re.search(r'score mate (-?\d+)', line)
            if match:
                return int(match.group(1))*1000
        if 'score cp' in line:
            match = re.search(r'score cp (-?\d+)', line)
            if match:
                return int(match.group(1))
    return 0
def _parse_win_rate(win: int) -> int:
    """convert winning rate to winning rate."""
    return 0 if win == 0 else win/100

def analyze_fen(fen_full: str, is_red: bool, board_array: list) -> dict:
    """
    Analyzes a FEN string, saves the results to the database, and returns the best move.
    """
    with get_db() as db:
        # 1. Get cloud analysis and save to DB
        cloud_moves = get_chessdb_analysis(fen_full,is_red, board_array)
        if cloud_moves:
            logger.info(f"[analysis] cloud_moves: {cloud_moves}")
            add_analysis_to_db(db, cloud_moves)
            # Get list first data
            best_move_list = cloud_moves[0]
            return {
                'fen': fen_full,
                'is_move': 'w' if is_red else 'b',
                'move': best_move_list.get('move'),
                'chinese_move': best_move_list.get('chinese_move'),
                'source': best_move_list.get('source'),
                'score': best_move_list.get('score'),
                'win_rate': _parse_win_rate(best_move_list.get('win_rate', 0))
            }

        # 2. Get local analysis
        fen = fen_full
        fen_parts = fen.split(' ')
        fen_board = fen_parts[0]
        side_to_move = fen_parts[1] if len(fen_parts) > 1 else 'w'
        best_move,line,fen_string = engine_instance.get_best_move(fen_board, side_to_move)
        logger.info(f"[analysis] lines: {line}, best_move: {best_move},fen_string: {fen_string}")
        if not is_valid_move_format(best_move):
            logger.error(f"Engine returned invalid move: {best_move}")
            return {"error": f"Invalid move format from engine: {best_move}"}
        
        # 3. Save local analysis to DB
        local_analysis_data = {
            'fen': fen_board,
            'is_move': side_to_move,
            'move': best_move,
            'chinese_move': convert_move_to_chinese(best_move, board_array, is_red),
            'source': 0,
            'score': _parse_engine_score(line),
            'win_rate': 9000
        }
        add_analysis_to_db(db, [local_analysis_data])

        # 4. Prepare and return the result
        local_analysis_data['fen'] = fen_full
        local_analysis_data['win_rate'] = _parse_win_rate(local_analysis_data['win_rate'])
        return local_analysis_data
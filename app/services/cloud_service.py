import requests
from app.logging_config import logger
from app.engine.board import convert_move_to_chinese, is_valid_move_format
import re

def _safe_int_parse(value, default=0):
    """Safely parses a string to an integer, returning a default value on failure."""
    if isinstance(value, str) and value.strip().lstrip('-').isdigit():
        return int(value.strip())
    elif isinstance(value, (int, float)):
        return int(value)
    return default

def _parse_win_rate(winrate_str):
    """
    解析 chessdb.cn 返回的 winrate 字段，返回 0-10000 的整数（百分比*100）。
    支持 '0.51', '51', '51%', '??' 等格式。
    """
    if not winrate_str or winrate_str == '??':
        return 0
    winrate_str = winrate_str.replace('%', '').strip()
    try:
        value = float(winrate_str)
    except Exception:
        return 0
    if 0 <= value <= 1:
        return int(value * 10000)
    elif 0 <= value <= 100:
        return int(value * 100)
    else:
        return 0

def get_chessdb_analysis(fen: str, is_red: bool, board_array: list):
    """
    Fetches analysis from chessdb.cn for a given FEN.
    """
    base_url = "https://www.chessdb.cn/chessdb.php"
    params = {
        'action': 'queryall',
        'learn': '1',
        'showall': '1',
        'board': fen
    }
    try:
        logger.info(f"[chessdb.cn] 请求URL: {base_url}")
        logger.info(f"[chessdb.cn] 请求参数: {params}")
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        content = response.text
        logger.info(f"[chessdb.cn] 返回内容: {content}")
        if not content or 'move' not in content:
            logger.warning(f"No valid data from chessdb.cn for FEN: {fen}")
            return []

        # Split FEN into board and side to move
        fen_parts = fen.split(' ')
        fen_board = fen_parts[0]
        side_to_move = fen_parts[1] if len(fen_parts) > 1 else 'w'


        moves_data = []
        parts = content.split('|')
        for part in parts:
            if not part: continue
            data = {}
            for item in part.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    data[key.strip()] = value.strip()
            
            if 'move' in data:
                try:
                    if 'score' in data and ('??' in str(data.get('score'))) and 'note' in data and ('??-??' in str(data.get('note'))):
                        continue 
                    logger.info(f"[chessdb.cn] 原始 winrate 字段: {data.get('winrate')}")
                    win_rate = _parse_win_rate(data.get('winrate', '0'))
                    logger.info(f"[chessdb.cn] 解析后 win_rate: {win_rate}")
                    moves_data.append({
                        'fen': fen_board,
                        'is_move': side_to_move,
                        'move': data.get('move'),
                        'chinese_move': convert_move_to_chinese(data.get('move'), board_array, is_red),
                        'source': 1,  # 1 for cloud source
                        'score': _safe_int_parse(data.get('score')),
                        'rank': _safe_int_parse(data.get('rank')),
                        'note': data.get('note', ''),
                        'win_rate': win_rate,
                    })
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing move data '{part}': {e}")

        
        if not moves_data:    
            logger.info(f'没有收录的棋局: {fen}')

        return moves_data

    except requests.RequestException as e:
        logger.error(f"Error fetching data from chessdb.cn: {e}")
        return [] 
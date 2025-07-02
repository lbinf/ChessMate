from typing import Tuple, Dict, Optional
import re

def is_valid_move_format(move: str) -> bool:
    """
    检查着法格式是否为 'a1a2'
    """
    if not isinstance(move, str) or len(move) != 4:
        return False
    # 格式: [a-i][0-9][a-i][0-9]
    return bool(re.match(r"^[a-i][0-9][a-i][0-9]$", move))

class ChessPiece:
    def __init__(self, name: str, color: str, position: Tuple[int, int]):
        self.name = name
        self.color = color
        self.position = position
    def __str__(self):
        return f"{self.color}的{self.name}在{self.position}"
    def to_dict(self):
        return {"name": self.name, "color": self.color, "position": self.position}

class ChessBoard:
    def __init__(self, fen_str: Optional[str] = None):
        self.pieces: Dict[Tuple[int, int], ChessPiece] = {}
        self.player_to_move = 'red'
        self.red_at_top = False
        self.col_names = {
            0: "一", 1: "二", 2: "三", 3: "四", 4: "五",
            5: "六", 6: "七", 7: "八", 8: "九"
        }
        self.row_names = {
            0: "1", 1: "2", 2: "3", 3: "4", 4: "5",
            5: "6", 6: "7", 7: "8", 8: "9", 9: "10"
        }
        self.chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
        self.piece_to_char = {
            ('车', 'red'): 'R', ('马', 'red'): 'N', ('相', 'red'): 'B', ('仕', 'red'): 'A', ('帅', 'red'): 'K', ('炮', 'red'): 'C', ('兵', 'red'): 'P',
            ('车', 'black'): 'r', ('马', 'black'): 'n', ('象', 'black'): 'b', ('士', 'black'): 'a', ('将', 'black'): 'k', ('炮', 'black'): 'c', ('卒', 'black'): 'p'
        }
        self.char_to_piece = {v: k for k, v in self.piece_to_char.items()}
        if fen_str:
            self._parse_fen(fen_str)
        else:
            self.initialize_board()
    def initialize_board(self):
        self.pieces.clear()
        red_pieces = [
            ('车', (0, 0)), ('马', (1, 0)), ('相', (2, 0)), ('仕', (3, 0)),
            ('帅', (4, 0)), ('仕', (5, 0)), ('相', (6, 0)), ('马', (7, 0)),
            ('车', (8, 0)), ('炮', (1, 2)), ('炮', (7, 2)),
            ('兵', (0, 3)), ('兵', (2, 3)), ('兵', (4, 3)), ('兵', (6, 3)), ('兵', (8, 3))
        ]
        for name, pos in red_pieces:
            self.pieces[pos] = ChessPiece(name, 'red', pos)
        black_pieces = [
            ('车', (0, 9)), ('马', (1, 9)), ('象', (2, 9)), ('士', (3, 9)),
            ('将', (4, 9)), ('士', (5, 9)), ('象', (6, 9)), ('马', (7, 9)),
            ('车', (8, 9)), ('炮', (1, 7)), ('炮', (7, 7)),
            ('卒', (0, 6)), ('卒', (2, 6)), ('卒', (4, 6)), ('卒', (6, 6)), ('卒', (8, 6))
        ]
        for name, pos in black_pieces:
            self.pieces[pos] = ChessPiece(name, 'black', pos)
        self.player_to_move = 'red'
        self._determine_orientation()

    def _determine_orientation(self):
        self.red_at_top = False
        for piece in self.pieces.values():
            if piece.name == '帅' and piece.color == 'red':
                if piece.position[1] < 5:
                    self.red_at_top = False
                return

    def add_piece(self,name,color,pos):
        self.pieces[pos] = ChessPiece(name, color, pos)

    def move_piece(self, from_pos: tuple, to_pos: tuple) -> str:
        if from_pos not in self.pieces:
            raise ValueError(f"起始位置 {from_pos} 没有棋子")
        piece_to_move = self.pieces[from_pos]
        notation = self.get_move_notation(piece_to_move, to_pos)
        if to_pos in self.pieces:
            del self.pieces[to_pos]
        del self.pieces[from_pos]
        piece_to_move.position = to_pos
        self.pieces[to_pos] = piece_to_move
        self.player_to_move = 'black' if self.player_to_move == 'red' else 'red'
        return notation

    def get_board_state(self) -> str:
        board = [['┼' for _ in range(9)] for _ in range(10)]
        for (x, y), piece in self.pieces.items():
            board[y][x] = piece.name
        board_str = "  1 2 3 4 5 6 7 8 9 \n"
        for row_idx, row in enumerate(reversed(board)):
            row_idx = abs(row_idx - 9)
            board_str += f"{self.row_names.get(row_idx, '?')} " + " ".join(row) + "\n"
        board_str += " 九 八 七 六 五 四 三 二 一\n"    
        return board_str

    def to_fen(self) -> str:
        fen_parts = []
        y_iterator = range(10) if self.red_at_top else reversed(range(10))
        for y in y_iterator:
            empty_count = 0
            row_fen = ""
            for x in range(9):
                pos = (x, y)
                if pos in self.pieces:
                    if empty_count > 0:
                        row_fen += str(empty_count)
                        empty_count = 0
                    piece = self.pieces[pos]
                    row_fen += self.piece_to_char.get((piece.name, piece.color), '?')
                else:
                    empty_count += 1
            if empty_count > 0:
                row_fen += str(empty_count)
            fen_parts.append(row_fen)
        board_fen = "/".join(fen_parts)
        player_char = 'w' if self.player_to_move == 'red' else 'b'
        return f"{board_fen} {player_char}"

    def __str__(self):
        return self.get_board_state()

    def _parse_fen(self, fen_str: str):
        self.pieces.clear()
        parts = fen_str.split()
        board_layout = parts[0].split('/')
        self.player_to_move = 'red' if parts[1].lower() == 'w' else 'black'
        for row_idx, fen_row in enumerate(board_layout):
            row_idx = abs(row_idx - 9)
            col_idx = 0
            for char in fen_row:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    piece_name, color = self.char_to_piece.get(char, ('?', '?'))
                    if piece_name != '?':
                        self.pieces[(col_idx, row_idx)] = ChessPiece(piece_name, color, (col_idx, row_idx))
                    col_idx += 1
        self._determine_orientation()

    def fen_to_board_array(self, fen: str):
        """
        Converts the board part of a FEN string into a 10x9 2D array.
        """
        board = []
        parts = fen.split(' ')
        fen_board = parts[0]
        rows = fen_board.split('/')
        for row_str in rows:
            row = []
            for char in row_str:
                if char.isdigit():
                    row.extend(['-'] * int(char))
                else:
                    row.append(char)
            # Ensure each row has 9 columns for a valid Xiangqi board
            if len(row) != 9:
                raise ValueError("Invalid FEN row length")
            board.append(row)
        # Ensure the board has 10 rows
        if len(board) != 10:
            raise ValueError("Invalid FEN number of rows")
        return board
    def get_move_notation(self, piece: 'ChessPiece', to_pos: tuple) -> str:
        from_pos = piece.position
        from_x, from_y = from_pos
        to_x, to_y = to_pos

        # 红方使用中文数字，从右到左数
        if piece.color == 'red':
            from_file = 9 - from_x
            to_file = 9 - to_x
            from_file_char = self.chinese_nums[from_file - 1]
            to_file_char = self.chinese_nums[to_file - 1]
        else: # 黑方使用阿拉伯数字，从左到右数
            from_file = from_x + 1
            to_file = to_x + 1
            from_file_char = str(from_file)
            to_file_char = str(to_file)
        # 判断移动类型
        if to_x != from_x and to_y != from_y:
            # 斜向移动（马、相、士等）
            # 红方：y增大为进，y减小为退
            # 黑方：y减小为进，y增大为退
            is_advancing = (to_y > from_y) if piece.color == 'red' else (to_y < from_y)
            action = "进" if is_advancing else "退"
            dest_char = to_file_char
        elif to_x != from_x:
            # 横向移动
            action = "平"
            dest_char = to_file_char
        else:
            # 纵向移动
            is_advancing = (to_y > from_y) if piece.color == 'red' else (to_y < from_y)
            action = "进" if is_advancing else "退"
            move_dist = abs(from_y - to_y)
            if piece.color == 'red':
                dest_char = self.chinese_nums[move_dist - 1]
            else:
                dest_char = str(move_dist)
        piece_prefix = piece.name
        same_col_pieces = [p for p in self.pieces.values() if p.name == piece.name and p.color == piece.color and p.position[0] == from_x and p.position != from_pos]
        if same_col_pieces:
            is_front = (from_y < same_col_pieces[0].position[1]) if piece.color == 'red' else (from_y > same_col_pieces[0].position[1])
            piece_prefix = ('前' if is_front else '后') + piece.name
        return f"{piece_prefix}{from_file_char}{action}{dest_char}"

    def move_to_coords(self,move):
        """
        将中国象棋着法（如 'a1a2'）转换为坐标移动（起点、终点）
        Args:
            move (str): 形如 'a1a2' 的着法
        Returns:
            tuple: (start_col, start_row, end_col, end_row)
        """
        if not is_valid_move_format(move):
            raise ValueError(f"Invalid move format: {move}")
        start_col_char, start_row_str, end_col_char, end_row_str = move[0], move[1], move[2], move[3]
        start_row = int(start_row_str)
        end_row = int(end_row_str)
        start_col = ord(start_col_char) - ord('a')
        end_col = ord(end_col_char) - ord('a')
        return (start_col, start_row, end_col, end_row)

    def coords_to_move(self,start_col, start_row, end_col, end_row):
        """
        将坐标移动（起点、终点）转换为中国象棋着法（如 'a1a2'）
        Args:
            start_col (int): 起点列（0-8）
            start_row (int): 起点行（0-9）
            end_col (int): 终点列（0-8）
            end_row (int): 终点行（0-9）
        Returns:
            str: 形如 'a1a2' 的着法
        """
        if not (0 <= start_col <= 8 and 0 <= end_col <= 8 and 0 <= start_row <= 9 and 0 <= end_row <= 9):
            raise ValueError("Column must be 0-8 and row must be 0-9")
        move = f"{chr(ord('a') + start_col)}{start_row}{chr(ord('a') + end_col)}{end_row}"
        return move

    def parse_ucci_move(self, ucci_move: str) -> tuple or None:
        """
        Parses a UCCI move string (e.g., 'h2e2') into board coordinates.
        UCCI坐标: files 'a'-'i' (左到右), ranks '0'-'9' (底到顶)
        内部坐标: x 0-8 (左到右), y 0-9 (顶到下, 红在顶)
        """
        if len(ucci_move) != 4:
            print("Invalid UCCI move format. It should be 4 characters, e.g., 'h2e2'.")
            return None
        f1, r1, f2, r2 = ucci_move[0], ucci_move[1], ucci_move[2], ucci_move[3]
        if not ('a' <= f1 <= 'i' and 'a' <= f2 <= 'i'):
            print("Invalid file in UCCI move. Files should be 'a' through 'i'.")
            return None
        if not ('0' <= r1 <= '9' and '0' <= r2 <= '9'):
            print("Invalid rank in UCCI move. Ranks should be '0' through '9'.")
            return None
        x1 = ord(f1) - ord('a')
        y1 = int(r1)
        x2 = ord(f2) - ord('a')
        y2 = int(r2)
        return x1, y1, x2, y2

    def get_board_array(self) -> list:
        """
        返回一个表示棋盘状态的二维列表 (10x9)。
        """
        board_array = [['.' for _ in range(9)] for _ in range(10)]
        for (x, y), piece in self.pieces.items():
            board_array[y][x] = piece.name
        return board_array

    def handle_ucci_move(self, ucci_move: str):
        try:
            coords = self.parse_ucci_move(ucci_move)
            if not coords:
                return
            x1, y1, x2, y2 = coords
            print(f"{x1},{y1}->{x2},{y2}")
            piece = self.pieces.get((x1, y1))
            if piece is None:
                print(f"Error: No piece at the starting position ({x1}, {y1}) for UCCI move '{ucci_move}'.")
                return
            current_color = 'red' if self.player_to_move == 'red' else 'black'
            if piece.color != current_color:
                print(f"Error: It's {current_color}'s turn, but the piece at ({x1}, {y1}) is {piece.color}.")
                return
            notation = self.get_move_notation(piece, (x2, y2))
            print(f"UCCI Move: {ucci_move}")
            print(f"Move Coordinates: from ({x1}, {y1}) to ({x2}, {y2})")
            print(f"Chinese Notation (着法): {notation}")
            # 移动棋子并获取记谱法
            color_str = "红方" if piece.color == 'red' else "黑方"
            move_desc = f"{piece.name}({x1}, {y1}) -> ({x2}, {y2})"
            notation = self.move_piece((x1,y1), (x2,y2))
            print(f"移动: {color_str} {move_desc} ({notation})")
            print()
            # Print the new FEN string after the move
            print(f"New FEN: {self.to_fen()}")
        except Exception as e:
            import traceback
            print(f"An error occurred while handling UCCI move '{ucci_move}': {e}")
            traceback.print_exc()

    def parse_chinese_notation(self, notation: str) -> tuple:
        """解析中文记谱法，返回起始和目标坐标"""
        # 棋子名称映射
        piece_names = {
            '车': '车', '马': '马', '相': '相', '象': '象', '仕': '仕', '士': '士', 
            '帅': '帅', '将': '将', '炮': '炮', '兵': '兵', '卒': '卒'
        }
        # 中文数字映射
        chinese_to_arabic = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9
        }
        # 阿拉伯数字映射
        arabic_to_arabic = {str(i): i for i in range(1, 10)}
        try:
            # 确定是哪一方的棋子
            is_red = False
            for piece_name in ['相', '仕', '帅', '兵']:
                if piece_name in notation:
                    is_red = True
                    break
            # 提取棋子名称
            piece_name = None
            for name in piece_names:
                if name in notation:
                    piece_name = name
                    break
            if not piece_name:
                raise ValueError("无法识别棋子名称")
            # 提取起始位置
            start_pos = None
            for char in notation:
                if char in chinese_to_arabic:
                    if is_red:
                        start_col = 9 - chinese_to_arabic[char]
                    else:
                        start_col = chinese_to_arabic[char] - 1
                    start_pos = char
                    break
                elif char in arabic_to_arabic:
                    if not is_red:
                        start_col = arabic_to_arabic[char] - 1
                        start_pos = char
                        break
            if not start_pos:
                raise ValueError("无法识别起始位置")
            # 确定起始行
            if is_red:
                if piece_name in ['车', '马', '相', '仕', '帅']:
                    start_row = 0
                elif piece_name == '炮':
                    start_row = 2
                elif piece_name == '兵':
                    start_row = 3
            else:
                if piece_name in ['车', '马', '象', '士', '将']:
                    start_row = 9
                elif piece_name == '炮':
                    start_row = 7
                elif piece_name == '卒':
                    start_row = 6
            # 提取动作和目标位置
            action = None
            target_pos = None
            if '进' in notation:
                action = '进'
                for char in notation[notation.index('进')+1:]:
                    if char in chinese_to_arabic:
                        if is_red:
                            target_col = 9 - chinese_to_arabic[char]
                        else:
                            target_col = chinese_to_arabic[char] - 1
                        target_pos = char
                        break
                    elif char in arabic_to_arabic:
                        if not is_red:
                            target_col = arabic_to_arabic[char] - 1
                            target_pos = char
                            break
            elif '退' in notation:
                action = '退'
                for char in notation[notation.index('退')+1:]:
                    if char in chinese_to_arabic:
                        if is_red:
                            target_col = 9 - chinese_to_arabic[char]
                        else:
                            target_col = chinese_to_arabic[char] - 1
                        target_pos = char
                        break
                    elif char in arabic_to_arabic:
                        if not is_red:
                            target_col = arabic_to_arabic[char] - 1
                            target_pos = char
                            break
            elif '平' in notation:
                action = '平'
                for char in notation[notation.index('平')+1:]:
                    if char in chinese_to_arabic:
                        if is_red:
                            target_col = 9 - chinese_to_arabic[char]
                        else:
                            target_col = chinese_to_arabic[char] - 1
                        target_pos = char
                        break
                    elif char in arabic_to_arabic:
                        if not is_red:
                            target_col = arabic_to_arabic[char] - 1
                            target_pos = char
                            break
            if not action or not target_pos:
                raise ValueError("无法识别动作或目标位置")
            # 确定目标行和列
            if action == '平':
                target_row = start_row
            else:
                if action == '进':
                    if piece_name in ['车', '炮', '兵', '卒']:
                        target_col = start_col
                        target_row_char = None
                        for char in notation[notation.index('进')+1:]:
                            if char in chinese_to_arabic:
                                target_row_char = char
                                break
                            elif char in arabic_to_arabic:
                                target_row_char = char
                                break
                        if target_row_char:
                            if target_row_char in chinese_to_arabic:
                                target_row = start_row + chinese_to_arabic[target_row_char]
                            else:
                                target_row = start_row + arabic_to_arabic[target_row_char]
                        else:
                            if is_red:
                                target_row = start_row + 1
                            else:
                                target_row = start_row - 1
                    else:
                        if is_red:
                            target_row = start_row + 1
                        else:
                            target_row = start_row - 1
                else:  # action == '退'
                    if piece_name in ['车', '炮', '兵', '卒']:
                        target_col = start_col
                        target_row_char = None
                        for char in notation[notation.index('退')+1:]:
                            if char in chinese_to_arabic:
                                target_row_char = char
                                break
                            elif char in arabic_to_arabic:
                                target_row_char = char
                                break
                        if target_row_char:
                            if target_row_char in chinese_to_arabic:
                                target_row = start_row - chinese_to_arabic[target_row_char]
                            else:
                                target_row = start_row - arabic_to_arabic[target_row_char]
                        else:
                            if is_red:
                                target_row = start_row - 1
                            else:
                                target_row = start_row + 1
                    else:
                        if is_red:
                            target_row = start_row - 1
                        else:
                            target_row = start_row + 1
            return ((start_col, start_row), (target_col, target_row))
        except Exception as e:
            raise ValueError(f"解析记谱法失败: {e}")

    def engine_move_to_chinese_notation(self, engine_move: str) -> str:
        """
        将引擎着法转换为中文描述
        
        算法说明：
        1. 解析引擎着法（如 c7d7）
        2. 根据棋盘状态确定棋子类型
        3. 转换为中文坐标系统
        4. 生成中文着法描述
        
        Args:
            engine_move: 引擎着法（如 "c7d7"）
            
        Returns:
            str: 中文着法描述
        """
        coords = self.parse_ucci_move(engine_move)
        if not coords:
            raise ValueError(f"无效的引擎着法格式: {engine_move}")

        from_x, from_y, to_x, to_y = coords
        from_pos = (from_x, from_y)
        to_pos = (to_x, to_y)

        piece = self.pieces.get(from_pos)
        if not piece:
            raise ValueError(f"起始位置 {from_pos} 没有棋子")
            
        return self.get_move_notation(piece, to_pos)

    def is_in_check(self, color: str) -> bool:
        """
        检查指定颜色的王是否被将军
        """
        king_pos = None
        king_name = '帅' if color == 'red' else '将'
        
        # 找到王的位置
        for pos, piece in self.pieces.items():
            if piece.name == king_name and piece.color == color:
                king_pos = pos
                break
        
        if not king_pos:
            return True # 如果王不存在，也算被将军（已经被吃了）

        # 检查所有对方棋子是否能攻击到王
        opponent_color = 'black' if color == 'red' else 'red'
        for pos, piece in self.pieces.items():
            if piece.color == opponent_color:
                possible_moves = self._get_piece_moves(pos)
                if king_pos in possible_moves:
                    # logger.info(f"{piece} at {pos} is checking the king at {king_pos}")
                    return True
        return False

    def _get_piece_moves(self, pos: Tuple[int, int]) -> list:
        """获取指定位置棋子的所有合法移动位置"""
        if pos not in self.pieces:
            return []
            
        piece = self.pieces[pos]
        moves = []
        
        # 各个棋子的走法规则
        if piece.name in ['车', '炮']:
            # 车和炮的直线移动
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                path_clear = True
                for i in range(1, 10):
                    nx, ny = pos[0] + dx * i, pos[1] + dy * i
                    if not (0 <= nx < 9 and 0 <= ny < 10):
                        break
                    
                    if (nx, ny) not in self.pieces:
                        if piece.name == '车':
                            moves.append((nx, ny))
                    else:
                        if piece.name == '车' and self.pieces[(nx, ny)].color != piece.color:
                            moves.append((nx, ny)) # 车可以吃子
                        
                        if path_clear: # 炮的炮架
                            path_clear = False
                            continue

                        if piece.name == '炮' and self.pieces[(nx, ny)].color != piece.color:
                            moves.append((nx, ny)) # 炮翻山吃子
                        break

        elif piece.name == '马':
            # 马走日
            for dx, dy in [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                leg_x, leg_y = pos[0] + (1 if dx > 0 else -1 if dx < 0 else 0), pos[1] + (1 if dy > 0 else -1 if dy < 0 else 0)
                if abs(dx) == 2: leg_x = pos[0] + (1 if dx>0 else -1)
                else: leg_y = pos[1] + (1 if dy>0 else -1)
                
                if (leg_x, leg_y) in self.pieces: # 蹩马腿
                    continue
                if 0 <= nx < 9 and 0 <= ny < 10:
                    if (nx, ny) not in self.pieces or self.pieces[(nx, ny)].color != piece.color:
                        moves.append((nx, ny))

        elif piece.name in ['相', '象']:
            # 相/象走田
            for dx, dy in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                eye_x, eye_y = pos[0] + dx // 2, pos[1] + dy // 2
                
                if (eye_x, eye_y) in self.pieces: # 塞象眼
                    continue
                
                # 不能过河
                if (piece.color == 'red' and ny > 4) or (piece.color == 'black' and ny < 5):
                    continue

                if 0 <= nx < 9 and 0 <= ny < 10:
                    if (nx, ny) not in self.pieces or self.pieces[(nx, ny)].color != piece.color:
                        moves.append((nx, ny))
                        
        elif piece.name in ['仕', '士']:
            # 士/仕走斜线
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                # 九宫格限制
                if not (3 <= nx <= 5 and ((0 <= ny <= 2) if piece.color == 'red' else (7 <= ny <= 9))):
                    continue
                if 0 <= nx < 9 and 0 <= ny < 10:
                    if (nx, ny) not in self.pieces or self.pieces[(nx, ny)].color != piece.color:
                        moves.append((nx, ny))
                        
        elif piece.name in ['帅', '将']:
            # 将/帅走直线
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = pos[0] + dx, pos[1] + dy
                # 九宫格限制
                if not (3 <= nx <= 5 and ((0 <= ny <= 2) if piece.color == 'red' else (7 <= ny <= 9))):
                    continue
                if 0 <= nx < 9 and 0 <= ny < 10:
                    if (nx, ny) not in self.pieces or self.pieces[(nx, ny)].color != piece.color:
                        moves.append((nx, ny))
            # 王对王
            opponent_king_name = '将' if piece.color == 'red' else '帅'
            for other_pos, other_piece in self.pieces.items():
                if other_piece.name == opponent_king_name:
                    if other_pos[0] == pos[0]:
                        is_clear = True
                        for y_check in range(min(pos[1], other_pos[1]) + 1, max(pos[1], other_pos[1])):
                            if (pos[0], y_check) in self.pieces:
                                is_clear = False
                                break
                        if is_clear:
                            moves.append(other_pos)
                    break
        
        elif piece.name in ['兵', '卒']:
            # 兵/卒
            if piece.color == 'red':
                # 向前
                if pos[1] < 9 and ((pos[0], pos[1] + 1) not in self.pieces or self.pieces[(pos[0], pos[1] + 1)].color != 'red'):
                    moves.append((pos[0], pos[1] + 1))
                # 过河后可以左右移动
                if pos[1] > 4:
                    if pos[0] > 0 and ((pos[0] - 1, pos[1]) not in self.pieces or self.pieces[(pos[0] - 1, pos[1])].color != 'red'):
                         moves.append((pos[0] - 1, pos[1]))
                    if pos[0] < 8 and ((pos[0] + 1, pos[1]) not in self.pieces or self.pieces[(pos[0] + 1, pos[1])].color != 'red'):
                         moves.append((pos[0] + 1, pos[1]))
            else: # black
                # 向前
                if pos[1] > 0 and ((pos[0], pos[1] - 1) not in self.pieces or self.pieces[(pos[0], pos[1] - 1)].color != 'black'):
                    moves.append((pos[0], pos[1] - 1))
                # 过河后可以左右移动
                if pos[1] < 5:
                    if pos[0] > 0 and ((pos[0] - 1, pos[1]) not in self.pieces or self.pieces[(pos[0] - 1, pos[1])].color != 'black'):
                         moves.append((pos[0] - 1, pos[1]))
                    if pos[0] < 8 and ((pos[0] + 1, pos[1]) not in self.pieces or self.pieces[(pos[0] + 1, pos[1])].color != 'black'):
                         moves.append((pos[0] + 1, pos[1]))

        return moves
    
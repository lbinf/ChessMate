import numpy as np
import re
from sklearn.cluster import KMeans

# 中文数字映射
CHINESE_NUM = {0: '零', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九'}


# 判断某一方有没有走子
def check_repeat_position(array1, array2, is_red):
    if not array2:
        return False
    
    letter_change = False
    # upper_case_loss = False
    # 检查小写字母位置是否变化,以确定是不是黑棋走了一步
    for i in range(len(array1)):  # 遍历第一个数组的每一行
        for j in range(len(array1[i])):  # 遍历每一行的每一列
            # 检查哪一方
            letter = array1[i][j].islower() if is_red else array1[i][j].isupper()
            if letter and array1[i][j]!= array2[i][j]:  # 如果是小写(大写)字母且在两个数组中的对应位置字符不同
                letter_change = True  # 标记小写(大写)字母位置发生变化
                break  # 一旦发现有变化，就立即停止当前行的检查
        if letter_change:  # 如果在当前行发现了变化
            break  # 停止整个双层循环        
    # # 检查大写字母是否减少
    # upper_case_count1 = sum(1 for row in array1 for item in row if item.isupper())
    # upper_case_count2 = sum(1 for row in array2 for item in row if item.isupper())
    # if upper_case_count1 > upper_case_count2:
    #     upper_case_loss = True
    
    # 字母有变化即不是重复局面,取反返回
    return not letter_change

# 验证着法格式是否有效
def is_valid_move_format(move):
    """
    检查着法字符串格式是否为'a1a2'
    """
    return isinstance(move, str) and len(move) == 4 and move.isalnum()

# 棋子数组转为FEN棋局字符串(不含轮哪方走棋信息)
def switch_to_fen(array, is_red):
    """
    将棋盘数组转换为FEN字符串
    
    算法说明：
    1. 如果本方是黑方，需要反转棋盘（因为FEN标准是红方视角）
    2. 每行从左到右编码，连续的空位用数字表示
    3. 行与行之间用'/'分隔
    
    Args:
        array: 10x9的棋盘数组
        is_red: 本方是否为红方
        
    Returns:
        tuple: (FEN字符串, 处理后的棋盘数组)
    """
    # 容错：自动拍平嵌套 list，确保每一行是一维字符串列表
    fixed_array = []
    for idx, row in enumerate(array):
        if not isinstance(row, list):
            print(f"[switch_to_fen] Warning: row {idx} is not a list, but {type(row)}: {row}")
            continue
        if any(isinstance(cell, list) for cell in row):
            flat_row = []
            for cell in row:
                if isinstance(cell, list):
                    flat_row.extend(cell)
                else:
                    flat_row.append(cell)
            fixed_array.append(flat_row)
        else:
            fixed_array.append(row)
    array = fixed_array

    # 本方是黑方就反向遍历（FEN标准是红方视角）
    if not is_red:
        array = [row[::-1] for row in array[::-1]] 

    rows = []  
    for row in array:  
        # 初始化当前行的字符串和连续短横线计数器 
        row_str = []  
        empty_count = 0  

        # 遍历行中的每个元素  
        for cell in row:  
            if cell == '-':  
                # 如果当前是空位，增加连续空位的计数器  
                empty_count += 1 
            else:  
                # 如果是棋子，先处理之前的连续空位  
                if empty_count > 0:  
                    row_str.append(str(empty_count))  
                    empty_count = 0  
                # 添加非空元素  
                row_str.append(cell)  
  
        # 处理行末尾的连续空位  
        if empty_count > 0:  
            row_str.append(str(empty_count))  
  
        # 将当前行的字符串列表转换为单个字符串，并添加到结果列表中  
        rows.append(''.join(row_str))  

    # 保险：确保 rows 里全是字符串
    fen_string = "/".join([str(r) if not isinstance(r, str) else r for r in rows])

    # 新增：FEN格式校验
    if len(rows) != 10 or fen_string.count('/') != 9:
        print('[switch_to_fen] Invalid FEN rows or format! array:', array)
        # 返回标准初始局面
        default_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"
        return default_fen, array

    return fen_string, array

def convert_move_to_chinese(move, board_array, is_red):
    """
    将引擎着法转换为中文描述
    
    算法说明：
    1. 解析引擎着法（如 c7d7）
    2. 根据棋盘状态确定棋子类型
    3. 转换为中文坐标系统
    4. 生成中文着法描述
    
    Args:
        move: 引擎着法（如 "c7d7"）
        board_array: 棋盘数组
        is_red: 本方是否为红方
        
    Returns:
        str: 中文着法描述
    """
    # 只允许标准4位着法（如 a2b3），否则直接返回
    if not isinstance(move, str) or not re.match(r'^[a-i][0-9][a-i][0-9]$', move):
        return move

    # 健壮性检查
    if not isinstance(board_array, list) or len(board_array) != 10 or any(len(row) != 9 for row in board_array):
        print(f"[convert_move_to_chinese] Invalid board_array shape: {type(board_array)}, len={len(board_array) if isinstance(board_array, list) else 'N/A'}")
        return move

    PIECE_CODES = {
        'r': '车', 'n': '马', 'b': '象', 'a': '士', 'k': '将', 'p': '卒', 'c': '炮',
        'R': '车', 'N': '马', 'B': '相', 'A': '士', 'K': '帅', 'P': '兵', 'C': '炮', '-': '空'
    }

    try:
        # 解析着法
        start_col_char, start_row_str, end_col_char, end_row_str = move[0], move[1], move[2], move[3]
        start_row = int(start_row_str)
        end_row = int(end_row_str)
        start_col = ord(start_col_char) - ord('a')
        end_col = ord(end_col_char) - ord('a')

        # 检查索引合法性
        if not (0 <= start_col < 9 and 0 <= start_row < 10):
            print(f"[convert_move_to_chinese] move index out of range: {move}, start_col={start_col}, start_row={start_row}")
            return move
        piece_type = board_array[9 - start_row][start_col]
        piece_name = PIECE_CODES.get(piece_type, piece_type)

        # 转换为中文坐标
        # 红方视角：列从右到左1-9，行从上到下1-10
        start_col_chinese = CHINESE_NUM[(9 - start_col)] if is_red else (start_col + 1)
        end_col_chinese = CHINESE_NUM[(9 - end_col)] if is_red else (end_col + 1)
        crossed_row = CHINESE_NUM[abs(end_row - start_row)] if is_red else abs(end_row - start_row)

        name = piece_name
        
        # 处理同列同名棋子的情况
        if piece_type in ['r', 'R', 'n', 'N', 'c', 'C', 'p', 'P']:
            col_of_board = [row[start_col] for row in board_array]
            if col_of_board.count(piece_type) > 1:
                if col_of_board.index(piece_type) == 9 - start_row:
                    name = "前" if is_red else "后"
                else:
                    name = "后" if is_red else "前"
                start_col_chinese = piece_name

        # 生成着法描述
        if start_row == end_row:
            # 平移
            direction = "平"
            desc = f"{name}{start_col_chinese}{direction}{end_col_chinese}"
        else:
            # 前进或后退
            action1 = "进" if is_red else "退"
            action2 = "退" if is_red else "进"
            direction = action1 if start_row < end_row else action2
            
            if piece_type in ['r', 'R', 'c', 'C', 'p', 'P', 'k', 'K']:
                # 车、炮、卒、将帅：末尾数字是跨越的行数
                desc = f"{name}{start_col_chinese}{direction}{crossed_row}"
            else:
                # 马、象、士：末尾数字是终点所在列数
                desc = f"{name}{start_col_chinese}{direction}{end_col_chinese}"

        return desc
    except Exception as e:
        print(f"解析着法失败: {move}, 错误: {e}")
        return move

def fen_to_board_array(fen_board):
    """
    Converts the board part of a FEN string into a 10x9 2D array.
    """
    board = []
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
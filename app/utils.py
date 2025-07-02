import numpy as np
import re
from sklearn.cluster import KMeans

# 中文数字映射
CHINESE_NUM = {0: '零', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九'}

def cluster_lines(lines, axis='y', num_clusters=10):
    """
    使用K-Means聚类算法对检测到的线进行分组，并返回每组的中心点。
    这比旧的`keep_middle_lines`方法更健壮。

    Args:
        lines (list): Hough变换检测到的线的列表。
        axis (str): 'y'表示水平线聚类, 'x'表示垂直线聚类。
        num_clusters (int): 期望的簇数量 (10条水平线, 9条垂直线)。

    Returns:
        list: 包含每个簇中心点坐标的列表。
    """
    if lines is None or len(lines) < num_clusters:
        print(f"Warning: 检测到的线数量 ({len(lines) if lines else 0}) 少于期望的数量 ({num_clusters})。")
        # 即使线不够，也尝试返回坐标
        coords = [line[0][1] if axis == 'y' else line[0][0] for line in lines] if lines else []
        return sorted(list(set(coords)))

    # 提取用于聚类的坐标
    coords = [line[0][1] if axis == 'y' else line[0][0] for line in lines]
    coords_reshaped = np.array(coords).reshape(-1, 1)

    # 使用K-Means进行聚类
    try:
        kmeans = KMeans(n_clusters=num_clusters, n_init=10, random_state=0).fit(coords_reshaped)
        # 获取聚类中心并排序
        centroids = sorted([int(center[0]) for center in kmeans.cluster_centers_])
        return centroids
    except Exception as e:
        print(f"Error during K-Means clustering: {e}")
        # 如果聚类失败，返回原始坐标的唯一值
        return sorted(list(set(coords)))

# 筛选水平线
def filter_horizontal_lines(lines, img_width):
    horizontal_lines = []
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                # 检查是否为水平线（允许有小的角度偏差）
                if abs(y1 - y2) < 10:
                    horizontal_lines.append(line)
    
    # 使用聚类获取精确的y坐标
    y_coords = cluster_lines(horizontal_lines, axis='y', num_clusters=10)
    
    # 为了兼容旧代码，我们仍然返回xMin和xMax，尽管它们可能不再那么重要
    xMin = float('inf')
    xMax = float('-inf')
    if horizontal_lines:
        x_coords = [line[0][0] for line in horizontal_lines] + [line[0][2] for line in horizontal_lines]
        xMin = min(x_coords) if x_coords else 0
        xMax = max(x_coords) if x_coords else img_width

    return y_coords, xMin, xMax

# 筛选竖直线
def filter_vertical_lines(lines, img_width):
    vertical_lines = []
    if lines is not None:
        for line in lines:
            for x1, y1, x2, y2 in line:
                # 检查是否为垂直线（允许有小的角度偏差）
                if abs(x1 - x2) < 10:
                    vertical_lines.append(line)

    # 使用聚类获取精确的x坐标
    x_coords = cluster_lines(vertical_lines, axis='x', num_clusters=9)

    # 为了兼容旧代码，我们仍然返回yMin和yMax
    yMin = float('inf')
    yMax = float('-inf')
    if vertical_lines:
        y_coords = [line[0][1] for line in vertical_lines] + [line[0][3] for line in vertical_lines]
        yMin = min(y_coords) if y_coords else 0
        yMax = max(y_coords) if y_coords else img_width

    return x_coords, yMin, yMax

# 截取棋子图片名称中的字母代号
def cut_substring(string):
    # 处理None值的情况
    if string is None:
        return "unknown"
    
    index_ = string.find('_')
    index_dot = string.find('.')
    if index_!= -1 and index_dot!= -1:
        string = string[index_ + 1:index_dot]
        
    return string

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

    fen_string = "/".join(rows) + (' w' if is_red else ' b')
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
        
        # 获取棋子类型
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

def move_to_coords(move):
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

def coords_to_move(start_col, start_row, end_col, end_row):
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

# 示例：
# move = 'c2e3'
# coords = move_to_coords(move)  # (2, 2, 4, 3)
# move2 = coords_to_move(*coords)  # 'c2e3'
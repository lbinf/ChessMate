import cv2
import numpy as np
import os
import json
import logging
from app import utils

# 配置日志记录器
logger = logging.getLogger(__name__)

class FenRecognizerCore:
    """
    具体识别算法实现，负责图像处理、棋盘/棋子识别等。
    """
    
    def pre_processing_image(self, img_path):
        """
        图像预处理：读取图像并转换为灰度图。
        
        Args:
            img_path: str, 图像文件路径
            
        Returns:
            tuple: (原始图像, 灰度图像) 或 (None, None) 如果读取失败
        """
        img = cv2.imread(img_path)
        if img is None:
            logger.error(f"无法读取图像文件: {img_path}")
            return None, None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        logger.debug("图像预处理完成")
        return img, gray

    def get_board_data(self):
        """
        从JSON文件获取棋盘坐标数据。
        
        Returns:
            tuple: (x坐标数组, y坐标数组, 错误信息)
        """
        x_array = []
        y_array = []
        error = ''
        try:
            with open('./app/json/board.json', 'r') as file:
                data = json.load(file)
            x_array = data["x"]
            y_array = data["y"]
            logger.debug("成功从JSON文件读取棋盘坐标")
        except FileNotFoundError:
            error = '文件未找到'
            logger.warning("棋盘坐标JSON文件未找到")
        except json.JSONDecodeError:
            error = 'JSON解析错误'
            logger.error("棋盘坐标JSON文件格式错误")
        except Exception as e:
            error = str(e)
            logger.error(f"读取棋盘坐标时发生错误: {e}")
        return x_array, y_array, error

    def board_recognition(self, img, gray):
        """
        识别棋盘网格线。
        
        Args:
            img: ndarray, 原始图像
            gray: ndarray, 灰度图像
            
        Returns:
            tuple: (x坐标数组, y坐标数组)
        """
        x_array, y_array, error = self.get_board_data()
        if not error:
            logger.info("从JSON文件读取棋盘坐标")
            if len(x_array) == 9 and len(y_array) == 10:
                return x_array, y_array
            else:
                logger.warning("JSON文件中的棋盘坐标数据不完整，重新检测")

        logger.info("开始检测棋盘网格线...")
        gaus = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gaus, 30, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=60, minLineLength=80, maxLineGap=10)
        
        if lines is None:
            logger.warning("使用初始阈值未检测到线条，尝试降低阈值")
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=60, maxLineGap=15)
            
        if lines is None:
            logger.error("未能检测到任何线条，使用默认坐标")
            return [32, 146, 262, 376, 492, 608, 724, 840, 956], [30, 86, 144, 202, 260, 318, 374, 432, 490, 548]

        logger.info(f"检测到 {len(lines)} 条线")
        x_array, yMin, yMax = utils.filter_vertical_lines(lines, img.shape[1])
        y_array, xMin, xMax = utils.filter_horizontal_lines(lines, img.shape[1])
        logger.info(f"过滤后结果: 竖线{len(x_array)}条, 横线{len(y_array)}条")

        if len(x_array) < 9 or len(y_array) < 10:
            logger.error("未能检测到完整的棋盘网格，使用默认坐标")
            default_x = [32, 146, 262, 376, 492, 608, 724, 840, 956]
            default_y = [30, 86, 144, 202, 260, 318, 374, 432, 490, 548]
            data = {"x": default_x, "y": default_y}
            with open('./app/json/board.json', 'w') as file:
                json.dump(data, file)
            return default_x, default_y

        x_array.sort()
        y_array.sort()
        logger.debug(f"最终坐标 - 竖线: {x_array}")
        logger.debug(f"最终坐标 - 横线: {y_array}")

        # 保存坐标到JSON文件
        data = {"x": x_array, "y": y_array}
        try:
            with open('./app/json/board.json', 'w') as file:
                json.dump(data, file)
            logger.info("棋盘坐标已保存到JSON文件")
        except Exception as e:
            logger.error(f"保存棋盘坐标时发生错误: {e}")

        return x_array, y_array

    def pieces_recognition(self, img, gray, param):
        """
        识别棋子位置和类型。
        
        Args:
            img: ndarray, 原始图像
            gray: ndarray, 灰度图像
            param: dict, 识别参数
            
        Returns:
            list: 识别到的棋子列表，每个元素为 (x, y, r, piece_name)
        """
        width = img.shape[1]
        height = img.shape[0]
        maxRadius = int(width / 9 / 2)
        minRadius = int(0.5 * maxRadius)
        minDist = int(0.7 * width / 9)
        logger.info(f"棋子检测参数: 最小半径={minRadius}, 最大半径={maxRadius}, 最小距离={minDist}")

        circles_list = []
        param2_values = [12, 18, 24]
        param1_value = 50

        # 使用不同参数进行圆形检测
        for param2 in param2_values:
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, minDist,
                                     param1=param1_value, param2=param2,
                                     minRadius=minRadius, maxRadius=maxRadius)
            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                circles_list.extend(circles.tolist())
                logger.debug(f"参数(param1={param1_value}, param2={param2}): 检测到 {len(circles)} 个圆")

        # 去重并保留最佳检测结果
        if circles_list:
            circles_array = np.array(circles_list)
            unique_circles = []

            for circle in circles_array:
                x, y, r = circle
                # 检查是否与已有圆重叠
                is_duplicate = False
                for existing in unique_circles:
                    ex, ey, er = existing
                    distance = np.sqrt((x - ex) ** 2 + (y - ey) ** 2)
                    if distance < min(r, er):  # 如果圆心距离小于较小半径，认为是重复
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_circles.append(circle)

            circles = np.array(unique_circles)
            logger.info(f"去重后检测到 {len(circles)} 个棋子")
        else:
            circles = None
            logger.warning("未检测到任何棋子")

        pieces = []
        if circles is not None:
            for idx, (x, y, r) in enumerate(circles):
                try:
                    # 计算棋子区域
                    x1, y1, x2, y2 = x - r, y - r, x + r, y + r
                    x1, y1 = max(0, x1), max(0, y1)
                    x2 = min(img.shape[1] - 1, x2)
                    y2 = min(img.shape[0] - 1, y2)

                    if x2 <= x1 or y2 <= y1:
                        logger.warning(f"棋子{idx}: 无效的图像区域 ({x1},{y1}) to ({x2},{y2})")
                        continue

                    piece_slice = img[y1:y2 + 1, x1:x2 + 1]
                    if piece_slice.size == 0:
                        logger.warning(f"棋子{idx}: 空的图像区域")
                        continue

                    # 颜色识别
                    color = self.check_chess_piece_color_improved_v2(piece_slice)
                    if color is None:
                        logger.warning(f"棋子{idx}: 主要颜色检测失败，尝试备选方法")
                        color = self.check_chess_piece_color_alternative(piece_slice)
                        if color is None:
                            logger.warning(f"棋子{idx}: 所有颜色检测方法失败，使用默认红色")
                            color = 'red'

                    # 选择模板路径
                    platform = param.get('platform', 'JJ')
                    path_str = './app/images/jj' if platform == 'JJ' else './app/images/tiantian'

                    # 模板匹配
                    best_match, best_score = self.find_best_match_improved(piece_slice, path_str, color)
                    piece_name = self.get_piece_code_with_color(best_match, color)

                    if best_score >= 5:
                        pieces.append((x, y, r, piece_name))
                        logger.debug(f"棋子{idx}: 位置({x},{y}), 半径{r}, 类型{piece_name}, 匹配度{best_score:.2f}, 颜色{color}")
                    else:
                        logger.warning(f"棋子{idx}: 匹配度过低({best_score:.2f})，跳过")

                except Exception as e:
                    logger.error(f"处理棋子{idx}时发生错误: {e}", exc_info=True)
                    continue

        # 统计结果
        red_count = sum(1 for p in pieces if p[3].isupper())
        black_count = sum(1 for p in pieces if p[3].islower())
        logger.info(f"识别结果统计: 红方{red_count}个棋子, 黑方{black_count}个棋子")

        if red_count == 0:
            logger.warning("未检测到红方棋子，请检查图片质量或识别参数")
        if black_count == 0:
            logger.warning("未检测到黑方棋子，请检查图片质量或识别参数")

        return pieces

    def calculate_pieces_position(self, x_array, y_array, circles):
        """
        计算棋子在棋盘上的位置（修复版）
        
        算法步骤：
        1. 验证并修复棋盘坐标数组
        2. 初始化10行9列的棋盘数组
        3. 对每个棋子，找到最近的横线和竖线
        4. 在对应位置标记棋子
        5. 判断本方颜色（根据黑将位置）
        
        Args:
            x_array: 竖线x坐标数组（9列）
            y_array: 横线y坐标数组（10行）
            circles: 棋子信息列表
            
        Returns:
            tuple: (棋盘数组, 是否红方)
        """
        # 验证并修复棋盘坐标数组
        logger.debug(f"原始坐标数组: y_array长度={len(y_array)}, x_array长度={len(x_array)}")

        # 确保有足够的横线和竖线
        if len(y_array) < 10:
            logger.warning(f"Warning: 横线数量不足({len(y_array)})，使用默认值")
            # 根据实际图片尺寸生成合理的默认值
            if len(y_array) > 0:
                # 基于现有坐标推断
                step = y_array[-1] // len(y_array) if len(y_array) > 0 else 60
                y_array = [i * step for i in range(10)]
            else:
                y_array = [30, 86, 144, 202, 260, 318, 374, 432, 490, 548]

        if len(x_array) < 9:
            logger.warning(f"Warning: 竖线数量不足({len(x_array)})，使用默认值")
            if len(x_array) > 0:
                # 基于现有坐标推断
                step = x_array[-1] // len(x_array) if len(x_array) > 0 else 120
                x_array = [i * step for i in range(9)]
            else:
                x_array = [32, 146, 262, 376, 492, 608, 724, 840, 956]

        logger.debug(f"修复后坐标数组: y_array长度={len(y_array)}, x_array长度={len(x_array)}")
        logger.debug(f"横线坐标: {y_array}")
        logger.debug(f"竖线坐标: {x_array}")

        # 初始化棋盘数组 - 10行9列
        pieceArray = [["-"] * len(x_array) for _ in range(len(y_array))]

        logger.debug(f"初始化棋盘: {len(pieceArray)}行 x {len(pieceArray[0])}列")

        # 处理每个棋子
        for cx, cy, radius, name in circles:
            # 找到最接近的竖线和横线的索引
            nearest_x_index = self.find_nearest_index(cx, x_array)
            nearest_y_index = self.find_nearest_index(cy, y_array)

            # 边界检查
            if 0 <= nearest_y_index < len(pieceArray) and 0 <= nearest_x_index < len(pieceArray[0]):
                # 在棋盘数组中标记棋子位置
                pieceArray[nearest_y_index][nearest_x_index] = name
                logger.debug(f"棋子 {name} 映射到位置: 行{nearest_y_index}, 列{nearest_x_index} (坐标: x={cx}, y={cy})")
            else:
                logger.warning(f"Warning: 棋子 {name} 位置超出边界: y={nearest_y_index}, x={nearest_x_index}")

        # 判断本方是红棋还是黑棋
        # 寻找黑将(k)的位置来判断本方颜色
        # 黑将(k)在棋盘上方（前3行），红帅(K)在棋盘下方
        is_red = False
        black_king_found = False

        # 检查前3行是否有黑将
        for i in range(min(3, len(pieceArray))):
            for j in range(len(pieceArray[i])):
                if pieceArray[i][j] == 'k':  # 如果在前3行找到小写k（黑将），说明本方是红方
                    is_red = True
                    black_king_found = True
                    logger.info(f"在前{i}行找到黑将，本方为红方")
                    break
            if black_king_found:
                break

        # 如果没有找到黑将，检查后3行是否有红帅
        if not black_king_found:
            for i in range(max(0, len(pieceArray) - 3), len(pieceArray)):
                for j in range(len(pieceArray[i])):
                    if pieceArray[i][j] == 'K':  # 如果在后3行找到大写K（红帅），说明本方是黑方
                        is_red = False
                        logger.info(f"在后{len(pieceArray) - i}行找到红帅，本方为黑方")
                        break

        # 打印棋盘状态用于调试
        logger.debug("棋盘状态:")
        for i, row in enumerate(pieceArray):
            logger.debug(f"第{i}行: {row}")

        return pieceArray, is_red

    def check_chess_piece_color_improved_v2(self,img):
        """
        改进的棋子颜色检测算法 v2

        算法步骤：
        1. 转换到HSV颜色空间
        2. 定义更广泛的红色和黑色HSV范围
        3. 计算红色和黑色区域的面积
        4. 根据面积比例判断颜色

        Args:
            img: 棋子图像区域

        Returns:
            str: 'red' 或 'black' 或 None
        """
        if img is None or img.size == 0:
            logger.error(f"Error: img is None or empty (shape: {img.shape if img is not None else 'None'})")
            return None

        # 转换到HSV颜色空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if hsv is None or hsv.size == 0:
            logger.error(f"Error: Failed to convert image to HSV")
            return None

            # 定义更广泛的红色HSV阈值范围
        red_ranges = [
            ([0, 30, 30], [10, 255, 255]),  # 浅红色（降低饱和度要求）
            ([160, 30, 30], [180, 255, 255]),  # 深红色（跨越180度边界）
            ([0, 50, 50], [10, 255, 255]),  # 中等红色
            ([0, 70, 70], [10, 255, 255]),  # 较暗红色
            ([0, 20, 20], [10, 255, 255])  # 更宽松的红色范围
        ]

        # 初始化红色掩码
        red_mask = np.zeros_like(hsv[:, :, 0])

        # 遍历每个红色范围并更新掩码
        for lower, upper in red_ranges:
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            red_mask_temp = cv2.inRange(hsv, lower, upper)
            red_mask = cv2.bitwise_or(red_mask, red_mask_temp)

            # 黑色检测：更宽松的黑色范围
        # 黑色棋子的特征：低亮度，低饱和度
        black_ranges = [
            ([0, 0, 0], [180, 255, 80]),  # 标准黑色
            ([0, 0, 0], [180, 100, 100]),  # 较亮的黑色
            ([0, 0, 0], [180, 255, 120])  # 更亮的黑色
        ]

        black_mask = np.zeros_like(hsv[:, :, 0])
        for lower, upper in black_ranges:
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            black_mask_temp = cv2.inRange(hsv, lower, upper)
            black_mask = cv2.bitwise_or(black_mask, black_mask_temp)

        # 形态学操作去除噪点
        kernel = np.ones((3, 3), np.uint8)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        black_mask = cv2.morphologyEx(black_mask, cv2.MORPH_OPEN, kernel)

        # 计算红色和黑色区域的面积
        red_area = cv2.countNonZero(red_mask)
        black_area = cv2.countNonZero(black_mask)

        # 计算总面积用于归一化
        total_area = img.shape[0] * img.shape[1]
        red_ratio = red_area / total_area
        black_ratio = black_area / total_area

        logger.debug(f"颜色检测v2: 红色比例={red_ratio:.3f}, 黑色比例={black_ratio:.3f}")

        # 返回颜色判断结果
        # 降低阈值，提高检测率
        if red_ratio > 0.05 and red_ratio > black_ratio:  # 降低红色阈值
            return "red"
        elif black_ratio > 0.05 and black_ratio > red_ratio:  # 降低黑色阈值
            return "black"
        else:
            logger.debug(f"颜色检测不确定: 红色比例={red_ratio:.3f}, 黑色比例={black_ratio:.3f}")
            return None

    def find_best_match_improved(self,img, images_folder, color):
        """
        改进的模板匹配算法

        算法步骤：
        1. 根据颜色筛选模板图片
        2. 使用多种特征匹配方法
        3. 综合评分选择最佳匹配

        Args:
            img: 棋子图像
            images_folder: 模板图片文件夹路径
            color: 棋子颜色

        Returns:
            tuple: (最佳匹配文件名, 匹配分数)
        """
        # 初始化最高分和最佳匹配
        best_score = 0
        best_match = None

        # 检查文件夹是否存在
        if not os.path.exists(images_folder):
            logger.warning(f"Warning: Images folder {images_folder} does not exist")
            return "unknown.jpg", 0

        # 遍历images_folder中的所有图片
        for filename in os.listdir(images_folder):
            if filename.endswith('.jpg'):
                # 检查文件名是否与目标棋子颜色匹配
                if (color == 'red' and filename.startswith('red_')) or (
                        color == 'black' and filename.startswith('black_')):
                    local_img_path = os.path.join(images_folder, filename)
                    local_img = cv2.imread(local_img_path)
                    if local_img is not None:
                        # 计算两张图片的相似度（使用改进的特征匹配）
                        score = self.compare_feature_improved(img, local_img)
                        # 更新最高分和最佳匹配
                        if score > best_score:
                            best_score = score
                            best_match = filename

                            # 如果没有找到匹配，返回默认值
        if best_match is None:
            logger.warning(f"Warning: No match found for {color} piece, using default")
            if color == 'red':
                best_match = "red_K.jpg"  # 默认红色帅
            else:
                best_match = "black_k.jpg"  # 默认黑色将
            best_score = 0

        return best_match, best_score

    def compare_feature_improved(self,img1, img2):
        """
        改进的特征点匹配算法

        算法步骤：
        1. 使用SIFT检测特征点
        2. 使用FLANN匹配器进行快速匹配
        3. 应用比率测试过滤匹配点
        4. 返回有效匹配点数量

        Args:
            img1: 第一张图像
            img2: 第二张图像

        Returns:
            int: 有效匹配点数量
        """
        # 创建SIFT特征检测器
        sift = cv2.SIFT_create()

        # 检测特征点和描述符
        kp1, des1 = sift.detectAndCompute(img1, None)
        kp2, des2 = sift.detectAndCompute(img2, None)

        # 如果任一图像没有特征点，返回0
        if des1 is None or des2 is None:
            return 0

        # 使用FLANN匹配器（更快更准确）
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)

        # 进行k近邻匹配
        matches = flann.knnMatch(des1, des2, k=2)

        # 应用Lowe's ratio测试过滤匹配点
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:  # 调整比率阈值
                    good_matches.append(m)

        return len(good_matches)

    def check_chess_piece_color_alternative(self,img):
        """
        备用的颜色检测方法

        基于亮度和对比度的简单检测
        """
        if img is None or img.size == 0:
            return None

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 计算平均亮度
        mean_brightness = np.mean(gray)

        # 计算标准差（对比度）
        std_brightness = np.std(gray)

        logger.debug(f"备用颜色检测: 平均亮度={mean_brightness:.1f}, 标准差={std_brightness:.1f}")

        # 简单的阈值判断
        if mean_brightness > 100:  # 较亮的图像可能是红色
            return "red"
        elif mean_brightness < 80:  # 较暗的图像可能是黑色
            return "black"
        else:
            return None

    def get_piece_code_with_color(self,filename, color):
        """
        根据文件名和颜色获取正确的棋子代码

        Args:
            filename: 模板文件名，如 'red_K.jpg' 或 'black_k.jpg'
            color: 棋子颜色，'red' 或 'black'

        Returns:
            str: 正确的棋子代码，红方大写，黑方小写
        """
        # 提取基础棋子代码
        piece_code = utils.cut_substring(filename)

        # 根据颜色确定大小写
        if color == 'red':
            # 红方使用大写字母
            return piece_code.upper()
        else:
            # 黑方使用小写字母
            return piece_code.lower()

    def find_nearest_index(self,point, points):
        """
        找到最近点的索引（改进版）

        算法改进：
        1. 使用更精确的距离计算
        2. 添加边界检查
        3. 改进最近点选择逻辑

        Args:
            point: 目标点坐标
            points: 点坐标数组

        Returns:
            int: 最近点的索引
        """
        if not points:
            return 0

        # 计算到每个点的距离
        distances = []
        for p in points:
            distance = abs(point - p)
            distances.append(distance)

        # 找到最小距离的索引
        min_index = distances.index(min(distances))

        # 调试信息
        logger.debug(f"  点{point}到各点距离: {distances}, 最近点索引: {min_index}")

        return min_index
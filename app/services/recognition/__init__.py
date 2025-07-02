"""
棋盘识别模块的主入口
"""
import logging
from flask import current_app
from app.services.analysis import analyze_fen
from .core import FenRecognizerCore
from .base import BaseBoardRecognizer
from app import utils

# 配置日志记录器
logger = logging.getLogger(__name__)


class FenCompatibleRecognizer(BaseBoardRecognizer):
    """
    策略模式下的兼容识别器，组合调用FenRecognizerCore，
    保证与原recognition.py调用链完全一致。
    """

    def __init__(self):
        self.core = FenRecognizerCore()

    def recognize(self, image_path, param=None):
        """
        识别棋盘图片，返回FEN字符串和相关信息。

        Args:
            image_path: str, 图片路径
            param: dict, 可选的参数字典

        Returns:
            dict: 包含fen、board_array和is_red的字典
        """
        import os
        if param is None:
            param = {}
            
        # 删除旧的棋盘坐标缓存
        board_json_path = './app/json/board.json'
        if os.path.exists(board_json_path):
            try:
                os.remove(board_json_path)
                print("已删除旧的棋盘坐标缓存，将执行新的网格检测。")
            except OSError as e:
                print(f"Error deleting file {board_json_path}: {e}")
                
        # 执行识别流程
        image, gray = self.core.pre_processing_image(image_path)
        x_array, y_array = self.core.board_recognition(image, gray)
        pieces = self.core.pieces_recognition(image, gray, param)
        position, is_red = self.core.calculate_pieces_position(x_array, y_array, pieces)
        fen_str, board_array = utils.switch_to_fen(position, is_red)
        for i, row in enumerate(board_array):
            logger.info(f"{row}")
        
        return {
            "fen": fen_str,
            "board_array": board_array,
            "is_red": is_red
        }


# --- 策略注册表和激活识别器 ---
RECOGNIZER_REGISTRY = {
    'fen_compatible': FenCompatibleRecognizer(),
}
ACTIVE_RECOGNIZER = RECOGNIZER_REGISTRY['fen_compatible']


def recognize_board(image_path, param=None):
    """
    统一识别入口，便于后续切换不同识别算法。

    Args:
        image_path: str, 图片路径
        param: dict, 可选的参数字典

    Returns:
        dict: 包含fen、board_array和is_red的字典
    """
    return ACTIVE_RECOGNIZER.recognize(image_path, param)


def analyze_image(image_path, param):
    """
    分析图像并返回结果。

    Args:
        image_path: str, 图片路径
        param: dict, 参数字典

    Returns:
        dict: 分析结果
    """
    try:
        current_app.logger.info(f"开始分析图像: {image_path}，参数: {param}")
        recog_result = recognize_board(image_path, param)
        fen = recog_result['fen']
        board_array = recog_result['board_array']
        is_red_turn = recog_result['is_red']
        # current_app.logger.info(f"生成的FEN: {fen}")
        analysis_result = analyze_fen(fen, is_red_turn, board_array)
        return {
            'success': True,
            'recognition_result': analysis_result,
            'result': analysis_result  # 兼容测试用例
        }
    except Exception as e:
        current_app.logger.error(f"图像分析过程中发生严重错误: {e}", exc_info=True)
        return {
            'success': False,
            'message': f"An error occurred during image analysis: {str(e)}"
        } 
from .base import BoardRecognizerBase
from .core import FenRecognizerCore

class FenCompatibleRecognizer(BoardRecognizerBase):
    def __init__(self):
        self.core = FenRecognizerCore()
    def recognize(self, image_path: str, param: dict = None) -> dict:
        import os
        if param is None:
            param = {}
        board_json_path = './app/json/board.json'
        if os.path.exists(board_json_path):
            try:
                os.remove(board_json_path)
                print("已删除旧的棋盘坐标缓存，将执行新的网格检测。")
            except OSError as e:
                print(f"Error deleting file {board_json_path}: {e}")
        image, gray = self.core.pre_processing_image(image_path)
        x_array, y_array = self.core.board_recognition(image, gray)
        pieces = self.core.pieces_recognition(image, gray, param)
        position, is_red = self.core.calculate_pieces_position(x_array, y_array, pieces)
        fen_str, board_array = utils.switch_to_fen(position, is_red)
        return {
            "fen": fen_str,
            "board_array": board_array,
            "is_red": is_red
        }

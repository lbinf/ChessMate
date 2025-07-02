from .strategy import FenCompatibleRecognizer
from .base import RECOGNIZER_REGISTRY

# 注册策略
RECOGNIZER_REGISTRY['fen_compatible'] = FenCompatibleRecognizer()
ACTIVE_RECOGNIZER = RECOGNIZER_REGISTRY['fen_compatible']

def recognize_board(image_path, param=None):
    return ACTIVE_RECOGNIZER.recognize(image_path, param)

# 兼容原API
def analyze_image(image_path, param):
    from flask import current_app
    from app.services.analysis import analyze_fen
    try:
        current_app.logger.info(f"开始分析图像: {image_path}，参数: {param}")
        recog_result = recognize_board(image_path, param)
        fen = recog_result['fen']
        board_array = recog_result['board_array']
        is_red_turn = recog_result['is_red']
        current_app.logger.info(f"生成的FEN: {fen}")
        analysis_result = analyze_fen(fen, is_red_turn, board_array)
        return {
            'success': True,
            'recognition_result': analysis_result,
            'result': analysis_result
        }
    except Exception as e:
        current_app.logger.error(f"图像分析过程中发生严重错误: {e}", exc_info=True)
        return {
            'success': False,
            'message': f\"An error occurred during image analysis: {str(e)}\"
        }

from flask import Blueprint, request, jsonify, send_from_directory
from app.services.analysis import analyze_fen
from app.services.recognition import analyze_image
from app.services.parameter import get_params, set_param
from app.engine.board import fen_to_board_array, is_valid_move_format, convert_move_to_chinese
from app.logging_config import logger
import json
import os
from app.engine import engine_instance

api = Blueprint('api', __name__)

@api.route('/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Chess AI Helper is running"})

@api.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    try:
        # It's better to save uploads to a dedicated, configured folder
        # For now, let's ensure the 'app/uploads' directory exists
        upload_folder = os.path.join(os.getcwd(), 'app', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Use a secure filename and save the file
        from werkzeug.utils import secure_filename
        filename = secure_filename(file.filename)
        img_path = os.path.join(upload_folder, filename)
        file.save(img_path)

        param_str = request.form.get('param', '{}')
        param = json.loads(param_str)
        
        # Call the correct service function
        analysis_result = analyze_image(img_path, param)
        
        return jsonify(analysis_result)
    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/engine/command', methods=['POST'])
def send_engine_command():
    data = request.get_json()
    command = data.get('command') if data else None
    if command not in ['uci', 'isready', 'ucinewgame']:
        return jsonify({"error": "Invalid or missing command"}), 400
    output = getattr(engine_instance, command, lambda: "Invalid command")()
    return jsonify({"command": command, "output": output})

@api.route('/engine/params', methods=['GET', 'POST'])
def engine_params_route():
    if request.method == 'GET':
        return jsonify(get_params())
    data = request.get_json()
    name = data.get('param_name')
    value = data.get('param_value')
    params = set_param(name, value)
    return jsonify(params)

@api.route('/analyze_fen', methods=['POST'])
def analyze_fen_route():
    data = request.get_json()
    if not data or 'fen' not in data:
        logger.warning("/analyze_fen: 缺少FEN参数")
        return jsonify({"error": "Invalid JSON or missing 'fen' key"}), 400
    fen_full = data['fen'].strip()
    try:
        parts = fen_full.split(' ')
        fen_board = parts[0]
        side_char = parts[1].lower() if len(parts) > 1 else 'w'
        is_red = (side_char == 'w')
        board_array = fen_to_board_array(fen_board)
        result = analyze_fen(fen_full, is_red, board_array)
        logger.info(f"走法: {result}")
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f"/analyze_fen异常: {e}")
        return jsonify({'error': f'FEN analysis failed: {str(e)}'}), 500 

@api.route('/recevice', methods=['POST'])
def recevice_route():
    data = request.get_json()
   
    try:
        with open('data_received.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False))
            f.write('\n')
        return jsonify({'status':'success'})
        
    except Exception as e:
        logger.error(f"/recevice异常: {e}")
        return jsonify({'error': f'recevice: {str(e)}'}), 500         
import pytest
from app import app as flask_app
from app.services.recognition import recognize_board
import json
import os

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    upload_folder = "./test_uploads"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    flask_app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": upload_folder,
    })
    
    with flask_app.app_context():
        pass

    yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_engine_initial_state(client):
    """Check the initial state and parameters of the engine."""
    response = client.get('/api/engine/params')
    assert response.status_code == 200
    data = response.get_json()
    assert data['goParam'] == 'depth'
    assert data['depth'] == '20'

def test_engine_command_isready(client):
    """Test sending an 'isready' command to the engine."""
    response = client.post('/api/engine/command', json={'command': 'isready'})
    assert response.status_code == 200
    # The output might contain other info, so we check for inclusion
    assert 'readyok' in response.json['output']

def test_upload_file_and_analysis(client):
    """Test the file upload and analysis endpoint."""
    # This path should point to a test image within your project structure
    image_path = 'app/static/uploads/image.png' 
    
    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}, skipping upload test.")

    with open(image_path, 'rb') as img:
        # The 'param' must be sent as a string in the form data
        form_data = {
            'image': (img, 'test_board.png'),
            'param': (None, json.dumps({'platform': 'TT', 'autoModel': 'Off'}))
        }
        response = client.post('/api/upload', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
    assert 'result' in result
    
    analysis = result['result']
    assert 'fen' in analysis
    assert 'move' in analysis
    assert 'chinese_move' in analysis
    # assert 'board_array' in analysis
    # assert len(analysis['board_array']) == 10

def test_analyze_fen(client):
    resp = client.post('/api/analyze_fen', json={'fen': 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w'})
    assert resp.status_code == 200
    assert 'result' in resp.json

def test_engine_params_get(client):
    resp = client.get('/api/engine/params')
    assert resp.status_code == 200
    assert 'goParam' in resp.json

def test_fen_recognition_accuracy(client):
    """
    测试特定图片的FEN识别准确性
    """
    # 假设用于此测试的图片已放置在 tests/resources/ 目录下
    image_path = 'tests/resources/test_board_for_fen.png'
    expected_fen = "3a5/4a4/3k5/9/4P4/3C5/9/3ABA1r1/3rnpc2/4K4" # 忽略最后的 'w'

    if not os.path.exists(image_path):
        pytest.skip(f"测试图片未找到: {image_path}, 跳过此测试。")

    with open(image_path, 'rb') as img:
        form_data = {
            'image': (img, 'test_board_for_fen.png'),
            'param': (None, json.dumps({})) # 使用默认参数
        }
        response = client.post('/api/upload', data=form_data, content_type='multipart/form-data')

    assert response.status_code == 200
    result = response.get_json()
    
    if not result.get('success') or 'result' not in result or 'fen' not in result.get('result', {}):
        pytest.fail(f"API did not return a valid FEN. Response: {result}")

    # 断言生成的FEN与预期一致，如果失败则打印详细信息
    analysis_result = result['result']
    actual_fen = analysis_result['fen'].split(' ')[0]
    assert actual_fen == expected_fen, f"FEN识别不匹配！\n期望值: {expected_fen}\n实际值: {actual_fen}" 
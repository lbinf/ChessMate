import os
from flask import Flask
import logging
from app.config import Config
from app.shutdown import shutdown_manager

def create_app():
    # Let Flask use the default static and templates folders
    app = Flask(__name__)
    app.config.from_object(Config)
    from app.routes.api import api
    app.register_blueprint(api, url_prefix='/api')
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    return app

app = create_app()
logger = logging.getLogger(__name__)
logger.debug("app/__init__.py loaded, app id: %s", id(app))

from app.engine import engine_instance

# 使用Config.UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

def cleanup_engine():
    """
    清理引擎资源
    """
    if hasattr(engine_instance, 'close'):
        try:
            engine_instance.close()
        except Exception as e:
            logging.getLogger().error(f"Error during engine shutdown: {e}")

# 注册引擎清理函数（优先级较高，在日志关闭之前执行）
shutdown_manager.register(cleanup_engine, priority=100)

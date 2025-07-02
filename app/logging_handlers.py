"""
自定义日志处理器
"""
import logging
import sys

class ShutdownHandler(logging.StreamHandler):
    """
    专门用于关闭时的日志处理器
    """
    def __init__(self):
        super().__init__(sys.stderr)
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
        self._is_closed = False
    
    def emit(self, record):
        if not self._is_closed:
            try:
                super().emit(record)
                # 立即刷新输出
                self.flush()
            except Exception:
                pass
    
    def close(self):
        self._is_closed = True
        try:
            super().close()
        except Exception:
            pass 
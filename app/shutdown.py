"""
关闭序列管理模块
"""
import logging
import atexit
from typing import List, Callable
from functools import partial

class ShutdownManager:
    """
    管理应用程序的关闭序列
    """
    def __init__(self):
        self._shutdown_handlers: List[Callable] = []
        self._is_shutting_down = False
        
    def register(self, handler: Callable, priority: int = 0):
        """
        注册关闭处理函数
        
        Args:
            handler: 要执行的函数
            priority: 优先级（较大的数字先执行）
        """
        self._shutdown_handlers.append((priority, handler))
        self._shutdown_handlers.sort(key=lambda x: x[0], reverse=True)
    
    def execute_shutdown(self):
        """
        按优先级顺序执行所有关闭处理函数
        """
        if self._is_shutting_down:
            return
            
        self._is_shutting_down = True
        root_logger = logging.getLogger()
        
        for priority, handler in self._shutdown_handlers:
            try:
                handler()
            except Exception as e:
                try:
                    root_logger.error(f"Error in shutdown handler: {e}")
                except:
                    pass

# 创建全局实例
shutdown_manager = ShutdownManager()

# 注册关闭序列执行器
atexit.register(shutdown_manager.execute_shutdown) 
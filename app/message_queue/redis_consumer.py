"""
Redis消费者 - 用于跨项目迁移
"""
import json
import threading
import logging
import time
from typing import Optional, Callable
from datetime import datetime
import redis
from .chess_message_models import ChessMessage

logger = logging.getLogger(__name__)

class RedisConsumer:
    """Redis消息消费者"""
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: str = '123456',
                 queue_name: str = 'chess_message_queue'):
        """
        初始化Redis消费者
        
        Args:
            host: Redis主机地址
            port: Redis端口
            db: Redis数据库编号
            password: Redis密码
            queue_name: 队列名称
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.queue_name = queue_name
        self.handler: Optional[Callable] = None
        self.consumer_thread = None
        self.running = False
        
        # 创建Redis连接
        try:
            self.redis = redis.StrictRedis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # 测试连接
            self.redis.ping()
            print(f"✅ 成功连接到Redis: {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            raise

    def set_message_handler(self, handler: Callable[[ChessMessage], bool]):
        """
        设置消息处理器
        
        Args:
            handler: 消息处理函数，接收ChessMessage对象，返回处理是否成功
        """
        self.handler = handler
        print("✅ 消息处理器设置成功")

    def start_consumer(self, max_messages: Optional[int] = None):
        """
        启动消费者
        
        Args:
            max_messages (Optional[int]): 最大消费消息数量，消费后自动停止。默认为None，无限循环。
        """
        if self.running:
            print("⚠️ 消费者已在运行")
            return
            
        self.running = True
        self.consumer_thread = threading.Thread(target=self._consume_messages, args=(max_messages,), daemon=True)
        self.consumer_thread.start()
        print(f"✅ Redis消费者已启动，队列: {self.queue_name}")

    def stop_consumer(self):
        """停止消费者，增加对重复中断的健壮性"""
        if not self.running:
            return  # 已经在停止或已停止

        self.running = False
        if self.consumer_thread and self.consumer_thread.is_alive():
            print("\nℹ️ 正在等待消费线程退出...")
            try:
                # 等待线程自然结束
                self.consumer_thread.join(timeout=5)
            except KeyboardInterrupt:
                # 捕获在join期间的第二次Ctrl+C，防止堆栈跟踪
                print("\n⚠️ 检测到强制退出信号，将立即退出。")
            
            if self.consumer_thread.is_alive():
                print("⚠️ 消费线程未能在5秒内正常退出。程序将强制终止。")

        print("✅ Redis消费者已停止。")

    def _consume_messages(self, max_messages: Optional[int] = None):
        """
        消费消息
        
        Args:
            max_messages (Optional[int]): 最大消费消息数量。
        """
        consumed_count = 0
        while self.running:
            if max_messages is not None and consumed_count >= max_messages:
                print(f"ℹ️ 已达到指定消费数量 {max_messages}，消费者自动停止。")
                self.running = False
                break

            msg_dict = None # 在 try 外部初始化
            try:
                # 从Redis队列获取消息
                msg_json = self.redis.brpop(self.queue_name, timeout=1)
                if not msg_json:
                    continue
                
                consumed_count += 1
                    
                _, msg_str = msg_json
                msg_dict = json.loads(msg_str)
                
                # 直接将字典传递给处理器，不再反序列化为对象
                if self.handler:
                    try:
                        # 确保传递的是字典
                        result = self.handler(msg_dict)
                        message_type = result.get("message_type", "unknown")

                        if result.get("success"):
                            print(f"✅ 消息处理成功: {message_type}")
                        else:
                            error_msg = result.get('error', '未知错误')
                            print(f"❌ 消息处理失败: {message_type}, 原因: {error_msg}")
                            
                            # 失败消息转移到错误队列，使用原始字典
                            if msg_dict:
                                self.redis.lpush('chess_message_error_queue', json.dumps(msg_dict))
                                logger.warning(f"消息处理失败，已移入错误队列: {message_type}")

                    except Exception as e:
                        print(f"❌ 消息处理器异常: {e}")
                        # 处理器异常时，也将消息移入错误队列
                        if msg_dict:
                            self.redis.lpush('chess_message_error_queue', json.dumps(msg_dict))
                            logger.error(f"处理器异常，消息已移入错误队列: {e}", exc_info=True)
                        
            except json.JSONDecodeError as e:
                print(f"❌ 消息JSON解析失败: {e} - 原始消息: {msg_str}")
                # 将无法解析的原始字符串存入错误队列
                self.redis.lpush('chess_message_error_queue', msg_str)
                logger.error(f"无法解析的JSON消息已移入错误队列: {msg_str}")

            except Exception as e:
                print(f"❌ Redis消息消费失败: {e}")
                time.sleep(1)  # 避免频繁重试

    def get_queue_length(self) -> int:
        """获取队列长度"""
        try:
            return self.redis.llen(self.queue_name)
        except Exception as e:
            print(f"❌ 获取队列长度失败: {e}")
            return 0

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_consumer() 
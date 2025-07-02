import argparse
import time
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.message_queue.redis_consumer import RedisConsumer
from app.message_queue.chess_game_consumer import chess_message_processor
from app.message_queue.config import Config

def setup_logging():
    """配置全局日志记录"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "consumer.log")
    
    # 获取根logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 移除所有现有的handlers，避免重复日志
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # 格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 (滚动)
    # 2MB一个文件，最多保留5个
    file_handler = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logging.info("日志系统配置完成，将同时输出到控制台和文件。")

def main():
    """主函数，用于启动和管理消费者"""
    
    # 首先配置日志
    setup_logging()

    # 从配置中获取默认队列名
    default_queue = Config.get_queue_config().get('chess_message_queue', 'chess_message_queue')
    
    parser = argparse.ArgumentParser(description="运行象棋游戏消息消费者，方便调试。")
    parser.add_argument(
        "--queue",
        type=str,
        default=default_queue,
        help=f"要消费的Redis队列名称 (默认: {default_queue})"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="要消费的消息数量，消费完后自动退出 (默认: 无限循环)"
    )
    
    args = parser.parse_args()

    print(f"--- 消费者启动配置 ---")
    print(f"队列: {args.queue}")
    print(f"消费数量: {'无限' if args.count is None else args.count}")
    print("----------------------")

    # 获取Redis连接配置
    redis_config = Config.get_redis_config()

    try:
        consumer = RedisConsumer(
            host=redis_config.get('host'),
            port=redis_config.get('port'),
            password=redis_config.get('password'),
            db=redis_config.get('db'),
            queue_name=args.queue
        )

        consumer.set_message_handler(chess_message_processor.process_message)
        
        # 启动消费者，传入消费数量
        consumer.start_consumer(max_messages=args.count)
        
        # 等待消费者线程结束
        # 如果是无限循环，这里会一直阻塞，直到手动中断 (Ctrl+C)
        # 如果指定了count，线程会在消费完成后自动结束
        while consumer.consumer_thread.is_alive():
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nℹ️ 检测到手动中断 (Ctrl+C)，正在停止消费者...")
        consumer.stop_consumer()
    except Exception as e:
        print(f"❌ 启动消费者时发生致命错误: {e}")
    finally:
        print("✅ 消费者已安全退出。")

if __name__ == "__main__":
    main() 
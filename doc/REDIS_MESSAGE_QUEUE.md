# Redis 消息队列功能与使用说明

## 1. 功能简介
本模块用于中国象棋相关项目的消息异步处理，基于 Redis 队列实现消息分发、消费、错误重试等，适合分布式、解耦、异步处理场景。

This module provides asynchronous message processing for Xiangqi (Chinese Chess) projects, using Redis as the message queue backend. It supports distributed, decoupled, and asynchronous workflows.

---

## 2. 主要模块说明
- **redis_consumer.py**：核心 Redis 消费者，负责连接 Redis、拉取消息、回调处理、错误队列管理。
- **chess_game_consumer.py**：象棋业务消息处理器，负责解析和处理棋局相关消息（如开局、走子、结束等）。
- **chess_message_models.py**：定义消息结构（GameMessage、ChessMessage）和消息类型枚举（MessageType）。
- **config.py**：集中管理 Redis、队列、日志、消费者等配置，支持 .env 环境变量。

---

## 3. 消息结构说明
- **ChessMessage**
  - `message_type` (MessageType): 消息类型（如 chessmove_ack_msg、chessprotocol_ack_msg 等）
  - `data` (dict): 业务数据
  - `timestamp` (datetime): 消息时间戳
  - `source` (str): 消息来源
  - `priority` (int): 优先级（默认1）
- **GameMessage**
  - 兼容更通用的消息场景，字段同上，时间戳为字符串
- **MessageType**
  - 枚举所有支持的消息类型（如走子、开局、结束、认输等）

---

## 4. 配置方法
- 推荐通过 `.env` 文件或环境变量配置 Redis 连接、日志、消费者参数。
- 主要配置项：
  - `REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`、`REDIS_PASSWORD`
  - `LOG_LEVEL`、`LOG_FILE`
  - `CONSUMER_BATCH_SIZE`、`CONSUMER_TIMEOUT`、`CONSUMER_RETRY_COUNT`、`CONSUMER_RETRY_DELAY`
- 参考 `app/message_queue/config.py` 和 ENV_EXAMPLE 注释。

---

## 5. 依赖说明
- `redis>=4.0.0`  （Redis Python 客户端）
- `python-dotenv>=0.19.0`  （环境变量管理）
- Python 3.7+，标准库：logging, threading, dataclasses, enum, typing, json, datetime
- 详见 `requirements.txt`

---

## 6. 使用示例

### 启动 Redis 消费者
```python
from app.message_queue.redis_consumer import RedisConsumer
from app.message_queue.chess_game_consumer import chess_message_processor

# 实例化消费者
consumer = RedisConsumer(
    host='localhost', port=6379, db=0, password='123456', queue_name='chess_message_queue')

# 设置消息处理器（回调函数）
def handler(msg_dict):
    # 业务处理，推荐调用 chess_message_processor.process_message
    return chess_message_processor.process_message(msg_dict)

consumer.set_message_handler(handler)
consumer.start_consumer()  # 无限循环消费

# 停止消费者
# consumer.stop_consumer()
```

### 自定义消息处理器
```python
def my_handler(msg_dict):
    # 解析并处理消息
    print(msg_dict)
    return {"success": True, "message_type": msg_dict.get("message_type")}

consumer.set_message_handler(my_handler)
```

### 典型用法流程
1. 生产者将消息（dict/JSON）推入 Redis 队列（如 chess_message_queue）。
2. RedisConsumer 从队列拉取消息，自动调用 handler 处理。
3. 处理成功打印日志，失败消息自动转入错误队列（chess_message_error_queue）。
4. 支持多线程、可配置最大消费数量、健壮的异常处理。

---

## 7. 常见问题与建议
- Redis 连接失败请检查主机、端口、密码配置。
- handler 必须返回 dict，包含 `success` 字段。
- 消息格式建议遵循 ChessMessage/GameMessage 结构。
- 消费者支持上下文管理（with 语法），自动关闭线程。
- 错误消息会自动转移到错误队列，便于后续排查。

---

## 8. 适用场景
- 象棋对局消息异步处理、AI 分析、日志归档、分布式任务解耦等。
- 可扩展用于其他需要异步消息队列的 Python 项目。

---

## 9. 版本信息
- 本模块版本：1.0.0
- 主要作者：Chess Message Migration
- 依赖与更新请参考 requirements.txt 和源码注释。 
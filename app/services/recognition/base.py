"""
中国象棋棋盘识别策略模式基类和注册表。
定义了识别器的基本接口和策略注册机制。
"""
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod

@dataclass
class RecognitionResult:
    """识别结果数据类"""
    fen: str                    # FEN 字符串
    board_array: list[list[str]]  # 棋盘二维数组
    is_red: bool               # 是否红方

class BaseBoardRecognizer(ABC):
    """
    棋盘识别器的基类，定义了策略模式的接口。
    所有具体的识别器实现都应该继承这个类。
    """
    
    @abstractmethod
    def recognize(self, image_path, param=None):
        """
        识别棋盘图片，返回FEN字符串和相关信息。

        Args:
            image_path: str, 图片路径
            param: dict, 可选的参数字典

        Returns:
            dict: 包含以下键值对的字典：
                - fen: str, FEN字符串
                - board_array: list[list[str]], 棋盘二维数组
                - is_red: bool, 是否是红方
        """
        pass

class BoardRecognizerBase:
    """
    棋盘识别器基类。
    所有具体的识别策略都需要继承此类并实现 recognize 方法。
    """
    def recognize(self, image_path: str | Path, param: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        识别入口方法，子类必须实现。

        Args:
            image_path: 棋盘图片路径
            param: 可选的识别参数字典，如:
                  - platform: 平台类型 ('JJ'/'tiantian')
                  - threshold: 识别阈值
                  - debug: 是否输出调试信息

        Returns:
            Dict 包含:
            - fen: FEN 字符串
            - board_array: 棋盘二维数组
            - is_red: 是否红方视角
        """
        raise NotImplementedError("Subclasses must implement recognize()")

    @classmethod
    def register(cls, name: str) -> callable:
        """
        策略注册装饰器。
        用于将具体策略类注册到全局注册表。

        Args:
            name: 策略名称

        Returns:
            装饰器函数
        """
        def decorator(recognizer_cls: Type[BoardRecognizerBase]) -> Type[BoardRecognizerBase]:
            if not issubclass(recognizer_cls, BoardRecognizerBase):
                raise TypeError(f"{recognizer_cls.__name__} must inherit from BoardRecognizerBase")
            RECOGNIZER_REGISTRY[name] = recognizer_cls()
            return recognizer_cls
        return decorator

# 全局策略注册表
RECOGNIZER_REGISTRY: Dict[str, BoardRecognizerBase] = {}

# 当前激活的识别器
ACTIVE_RECOGNIZER: Optional[BoardRecognizerBase] = None

def get_recognizer(name: str) -> BoardRecognizerBase:
    """
    获取指定名称的识别器实例。

    Args:
        name: 识别器名称

    Returns:
        对应的识别器实例

    Raises:
        KeyError: 如果指定名称的识别器未注册
    """
    if name not in RECOGNIZER_REGISTRY:
        raise KeyError(f"Recognizer '{name}' not found. Available recognizers: {list(RECOGNIZER_REGISTRY.keys())}")
    return RECOGNIZER_REGISTRY[name]

def set_active_recognizer(name: str) -> None:
    """
    设置当前激活的识别器。

    Args:
        name: 识别器名称

    Raises:
        KeyError: 如果指定名称的识别器未注册
    """
    global ACTIVE_RECOGNIZER
    ACTIVE_RECOGNIZER = get_recognizer(name)

"""
图像处理相关的工具函数
"""
import numpy as np


def non_max_suppression(boxes, scores, threshold):
    """
    执行非最大抑制以消除重叠的边界框。

    Args:
        boxes: numpy array of shape (N, 4) containing bounding boxes
        scores: numpy array of shape (N,) containing confidence scores
        threshold: IoU threshold for suppression

    Returns:
        list: indices of boxes to keep
    """
    if len(boxes) == 0:
        return []

    # 如果边界框是整数，转换为浮点数
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    pick = []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(scores)

    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        overlap = (w * h) / area[idxs[:last]]

        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > threshold)[0])))

    return pick


def get_piece_code_from_filename(filename):
    """
    从模板文件名中提取棋子代码。

    Args:
        filename: str, 文件名，如 'red_K.jpg' 或 'black_p.jpg'

    Returns:
        str: 棋子代码，红方大写，黑方小写
    """
    import os
    base_name = os.path.splitext(filename)[0]
    if '_' not in base_name:
        return None

    parts = base_name.split('_')
    color_str, piece_char = parts[0], parts[1]

    return piece_char.upper() if color_str == 'red' else piece_char.lower() 
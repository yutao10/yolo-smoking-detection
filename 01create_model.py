from ultralytics import YOLO
import cv2
import os
import numpy as np

def load_yolo26_model(model_size: str = 'n') -> YOLO:
    """
    加载 YOLO26 模型
    
    参数:
        model_size: 模型尺寸，可选 'n', 's', 'm', 'l', 'x'
    
    返回:
        YOLO 模型对象
    """
    # 模型名称格式: yolo26{size}.pt
    # Ultralytics 会自动下载预训练权重
    model = YOLO(f'yolo26{model_size}.pt')
    print(f"✅ 成功加载 YOLO26-{model_size.upper()} 模型")
    return model
if __name__ == '__main__':
    # 加载模型
    model = load_yolo26_model('n')  # 使用 Nano 版本，加载速度快
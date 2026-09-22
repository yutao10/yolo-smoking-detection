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


def predict_webcam(model: YOLO, camera_index: int = 0):
    """
    实时摄像头目标检测
    
    参数:
        model: YOLO 模型对象
        camera_index: 摄像头索引，通常 0 是默认摄像头
    """
    cap = cv2.VideoCapture(camera_index)
    
    print("\n📹 实时摄像头检测开始（按 'q' 退出）")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 执行推理（设置 conf=0.5 过滤低置信度检测）
        results = model(frame, conf=0.5, stream=True)
        
        # 绘制结果
        for result in results:
            annotated_frame = result.plot()
        
        # 显示结果
        cv2.imshow('YOLO26 Real-time Detection', annotated_frame)
        
        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ 实时检测结束")
if __name__ == '__main__':
    try:
        # 先检查摄像头是否可用
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.release()
            print("   按 'q' 键退出实时检测")
            predict_webcam(model, camera_index=0)
        else:
            print("\n⚠️  无法访问摄像头，跳过实时摄像头推理演示")
    except Exception as e:
        print(f"\n⚠️  摄像头访问失败: {str(e)}，跳过实时摄像头推理演示")
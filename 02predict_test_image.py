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


def predict_single_image(model: YOLO, image_path: str, save_path: str = None):
    """
    对单张图像进行目标检测
    
    参数:
        model: YOLO 模型对象
        image_path: 输入图像路径
        save_path: 结果保存路径（可选）
    """
    # 执行推理
    # stream=True 启用流式推理，内存效率更高
    results = model(image_path, stream=True)
    
    # 处理结果
    for result in results:
        # result.boxes: 检测框信息
        # result.masks: 分割掩码（如果是分割模型）
        # result.keypoints: 关键点（如果是姿态模型）
        # result.probs: 分类概率（如果是分类模型）
        
        # 获取检测结果信息
        boxes = result.boxes
        print(f"\n📊 检测结果:")
        print(f"   检测到 {len(boxes)} 个目标")
        
        # 遍历每个检测框
        for i, box in enumerate(boxes):
            # 获取类别名称和置信度
            class_name = model.names[int(box.cls[0])]
            confidence = float(box.conf[0])
            # 获取边界框坐标 [x1, y1, x2, y2]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            print(f"   目标 {i+1}: {class_name} (置信度: {confidence:.2f})")
            print(f"      位置: [{int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}]")
        
        # 可视化结果
        annotated_image = result.plot()  # 返回带标注的图像
        
        # 如果指定了保存路径，保存结果
        if save_path:
            cv2.imwrite(save_path, annotated_image)
            print(f"✅ 结果已保存到: {save_path}")
        
        return annotated_image
if __name__ == '__main__':
    # 示例图片推理（需要提供测试图片）
    test_image_path = r'E:\yolo-images\2222.png'  # 请替换为实际图片路径
    if os.path.exists(test_image_path):
        predict_single_image(model, test_image_path, 'result.jpg')
    else:
        print(f"\n⚠️  测试图片 {test_image_path} 不存在，跳过图片推理演示")
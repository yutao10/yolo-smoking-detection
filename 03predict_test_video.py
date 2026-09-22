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


def predict_video(model: YOLO, video_path: str, output_path: str = 'output.mp4'):
    """
    对视频进行目标检测
    
    参数:
        model: YOLO 模型对象
        video_path: 输入视频路径（支持本地文件或摄像头索引）
        output_path: 输出视频路径
    """
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    
    # 获取视频属性
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    print(f"\n🎬 开始处理视频: {video_path}")
    print(f"   视频属性: {width}x{height}, {fps} FPS, {total_frames} 帧")
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 执行推理
        results = model(frame, stream=True)
        
        # 处理结果并绘制
        for result in results:
            annotated_frame = result.plot()
        
        # 写入输出视频
        out.write(annotated_frame)
        
        frame_count += 1
        if frame_count % 100 == 0:
            print(f"   已处理 {frame_count}/{total_frames} 帧")
    
    # 释放资源
    cap.release()
    out.release()
    print(f"✅ 视频处理完成，结果保存到: {output_path}")
if __name__ == '__main__':
    # 视频推理演示
    test_video_path = r'E:\yolo-images\video1.mp4'  # 请替换为实际视频路径
    if os.path.exists(test_video_path):
        predict_video(model, test_video_path, 'output.mp4')
    else:
        print(f"\n⚠️  测试视频 {test_video_path} 不存在，跳过视频推理演示")
        print("   提示：请在当前目录放置一个名为 test.mp4 的视频文件")
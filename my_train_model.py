from ultralytics import YOLO
if __name__ == '__main__':
    path1=r'E:\sx_yolo26\yolo26n.pt'
# 1. 加载预训练模型
    model = YOLO(path1)

# 2. 开始训练
    model.train(
    data='my_data.yaml',    # 你的数据集配置文件
    epochs=50,             # 训练轮数（新手50-100足够）
    imgsz=640,              # 图片尺寸
    batch=12,                # 批次大小（显存小就改2/4）
    device=0,               # 使用GPU（没有GPU就写device='cpu'）
    name='my_yolo_model2'    # 保存的模型名字
)
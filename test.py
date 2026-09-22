import torch
print(torch.cuda.is_available())  # 必须输出 True
print(torch.version.cuda)        # 输出 12.1
print(torch.__version__)         # 不能带 +cpu

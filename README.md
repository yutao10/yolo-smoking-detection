# YOLO26 烟雾检测系统

基于 **Ultralytics YOLO26** 的烟雾（smoke）目标检测项目，包含模型训练、Flask 后端服务与 uni-app 移动端前端，支持**拍照上传识别**和**实时摄像头检测**两种模式。

---

## 技术栈

- **模型**：YOLO26-n（轻量版，适合实时推理）
- **后端**：Python + Flask + OpenCV
- **前端**：uni-app（HBuilderX 开发，可编译到 H5 / App）
- **数据集**：YOLO 格式标注，单类别 `smoke`

---

## 文件说明

### 后端 & 训练

| 文件 | 作用 |
|---|---|
| `app2.py` | **主后端服务**，提供 `/detect`（图片检测）、`/video_feed`（实时视频流）、`/stop_video`、`/camera_check` 等接口 |
| `app1.py` | 基础版后端，仅提供 `/detect` 和 `/health`，不含视频流功能 |
| `my_train_model.py` | 模型训练脚本，加载 YOLO26-n 预训练权重，在自标数据集上微调 |
| `my_data.yaml` | 训练数据配置文件，定义数据集路径与类别信息 |

### 测试脚本（01 ~ 04，学习/调试用）

| 文件 | 作用 |
|---|---|
| `01create_model.py` | 加载 YOLO26-n 预训练权重，验证环境是否正常 |
| `02predict_test_image.py` | 对**单张图片**做检测，输出检测框坐标与置信度 |
| `03predict_test_video.py` | 对**本地视频文件**逐帧检测，结果保存为 `output.mp4` |
| `04predict_test_webcam.py` | 调用**电脑摄像头**实时检测，按 `q` 退出 |

> 注：01~04 是独立的入门练习脚本，不属于 Web 服务的运行链路，可单独运行。

### 前端

| 目录/文件 | 作用 |
|---|---|
| `yoloyolo/` | uni-app 项目完整源码 |
| `yoloyolo/pages/index/index.vue` | 主页面，包含拍照模式与实时检测模式 UI |
| `yoloyolo/manifest.json` | 应用配置（应用名称、图标、权限等） |
| `yoloyolo/pages.json` | 页面路由与导航栏配置 |

---

## 快速开始

### 1. 环境依赖

```bash
pip install flask flask-cors ultralytics opencv-python pillow numpy
```

> 首次运行 `ultralytics` 会自动下载 `yolo26n.pt` 预训练权重。

### 2. 准备模型权重

本仓库**未包含训练好的模型权重**（`.pt` 文件体积大，未上传）。

你需要将训练好的 `best.pt` 放到以下路径：

```
smoke_runs/detect/my_yolo_model-3/weights/best.pt
```

权重文件可通过以下方式获取：
- 运行 `my_train_model.py` 自行训练（需准备数据集）
- 从网盘/云盘下载作者提供的预训练权重

### 3. 启动后端

```bash
python app2.py
```

启动成功后将看到：

```
模型加载成功！
拍照检测接口: http://localhost:5000/detect
实时检测接口: http://localhost:5000/video_feed
 * Running on http://0.0.0.0:5000
```

### 4. 运行前端

使用 **HBuilderX** 打开 `yoloyolo` 文件夹：
- 「运行」→「运行到浏览器」或「运行到手机/模拟器」

---

## ⚠️ 使用者必须修改的地方

### 1. 后端 IP 地址（最重要）

打开 `yoloyolo/pages/index/index.vue`，找到第 178 行左右：

```javascript
apiUrl: 'http://192.168.220.92:5000'
```

**必须改成你自己电脑的局域网 IP**，否则前端请求会超时。

获取本机 IP 的方法（Windows）：
```bash
ipconfig
```
查看 `WLAN` 或 `无线局域网适配器` 下的 `IPv4 地址`。

> 提示：如果你的电脑 IP 是 `127.0.0.1`（仅本机浏览器访问），也可直接填 `http://127.0.0.1:5000`。手机/模拟器访问必须使用局域网 IP。

### 2. 模型权重路径

如果 `best.pt` 放在其他位置，需修改 `app2.py` 第 22 行左右的权重路径：

```python
model = YOLO(r'E:
epos	est_model-main	est1	est1
uns	rainest.pt')
```

### 3. 训练数据配置

如需重新训练，修改 `my_data.yaml` 中的数据集路径为你本地的实际路径。

---

## 功能说明

| 功能 | 入口 | 说明 |
|---|---|---|
| 拍照识别 | 前端「拍照模式」→「拍照识别」 | 上传图片到后端 `/detect`，返回画框结果 |
| 实时检测 | 前端「实时检测」 | 调用后端 `/video_feed`，MJPEG 流式传输，每 2 帧检测一次 |
| 摄像头控制 | 实时检测页面「停止」按钮 | 调用 `/stop_video` 释放摄像头资源 |

---

## 注意事项

1. **前后端需在同一局域网**：手机/模拟器与运行后端的电脑必须连接同一个 WiFi。
2. **IP 会变**：更换网络后电脑 IP 可能变化，需要重新修改 `index.vue` 中的 `apiUrl`。
3. **摄像头占用**：实时检测会占用电脑摄像头，同一时刻只能有一个程序使用。
4. **数据集未上传**：完整训练图片（约 924MB）未放入仓库，如需训练请自行准备或通过网盘获取。

---

## 项目结构

```
yolo-smoking-detection/
├── app2.py                 # 主后端（推荐）
├── app1.py                 # 基础后端
├── my_train_model.py       # 训练脚本
├── my_data.yaml            # 数据配置
├── 01create_model.py       # 环境验证
├── 02predict_test_image.py # 图片测试
├── 03predict_test_video.py # 视频测试
├── 04predict_test_webcam.py# 摄像头测试
├── yoloyolo/               # uni-app 前端源码
│   ├── pages/index/index.vue
│   ├── manifest.json
│   └── ...
└── .gitignore
```

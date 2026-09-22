# YOLO 物品识别后端 
import os
import cv2
import torch
import time
import numpy as np
import base64
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# 加载 YOLO 模型
MODEL_PATH = r'E:\sx_yolo26\smoke_runs\detect\my_yolo_model-3\weights\best.pt'
# MODEL_PATH = r'E:\sx_yolo26\hardhat_runs\detect\my_yolo_model2\weights\best.pt'

try:
    model = YOLO(MODEL_PATH)
    model.conf = 0.25
    print("模型加载成功！")
    print(f" 模型类别: {model.names}")
except Exception as e:
    print(f"模型加载失败: {e}")
    model = None

# 全局变量控制视频流
video_stream_active = False
camera = None
camera_lock = threading.Lock()
current_detections = []


def get_font():
    """获取中文字体"""
    font_paths = [
        "simhei.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, 20)
        except:
            continue
    return ImageFont.load_default()


def draw_boxes(image, detections):
    """在图像上绘制检测框"""
    try:
        img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        font = get_font()
        colors = {}

        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            label = det['label']
            confidence = det['confidence']

            if label not in colors:
                np.random.seed(hash(label) % 255)
                colors[label] = tuple(np.random.randint(0, 255, 3).tolist())
            color = colors[label]

            # 绘制矩形框
            draw.rectangle([x1, y1, x2, y2], outline=tuple(color), width=3)
            
            # 绘制标签背景
            text = f"{label} {confidence:.2f}"
            text_bbox = draw.textbbox((x1, y1), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # 确保标签在画面内
            y1_text = max(y1 - text_height - 4, 0)
            
            draw.rectangle([x1, y1_text, x1 + text_width + 4, y1], fill=tuple(color))
            draw.text((x1 + 2, y1_text + 2), text, fill=(255, 255, 255), font=font)

        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"绘制检测框失败: {e}")
        return image


def init_camera():
    """初始化摄像头"""
    global camera
    
    with camera_lock:
        if camera is not None:
            try:
                camera.release()
            except:
                pass
            camera = None
        
        # 尝试打开摄像头
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    camera = cap
                    print(f"摄像头已启动，索引: {i}")
                    return True
                else:
                    cap.release()
            except Exception as e:
                print(f"尝试打开摄像头 {i} 失败: {e}")
        
        return False


def release_camera():
    """释放摄像头资源"""
    global camera, video_stream_active
    
    video_stream_active = False
    
    with camera_lock:
        if camera is not None:
            try:
                camera.release()
            except:
                pass
            camera = None
            print("📹 摄像头已释放")
            return True
    return False


def generate_video_frames():
    """生成视频流帧"""
    global video_stream_active, camera, current_detections
    
    # 初始化摄像头
    if not init_camera():
        print("无法打开摄像头")
        # 返回错误帧
        error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(error_frame, "Camera Error - Please check camera", (100, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        _, buffer = cv2.imencode('.jpg', error_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        return
    
    frame_count = 0
    process_every_n_frames = 2  # 每2帧检测一次，提高性能
    
    while video_stream_active:
        frame = None
        
        with camera_lock:
            if camera is not None and camera.isOpened():
                success, frame = camera.read()
                if not success:
                    print("读取摄像头帧失败")
                    break
            else:
                print("摄像头未就绪")
                break
        
        if frame is None:
            break
        
        frame_count += 1
        current_frame = frame.copy()
        
        # 定期进行检测
        if frame_count % process_every_n_frames == 0:
            try:
                # YOLO检测
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = model(image_rgb, verbose=False)
                
                detections = []
                if results and len(results) > 0:
                    result = results[0]
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            label = model.names[cls]
                            detections.append({
                                'bbox': [x1, y1, x2, y2],
                                'label': label,
                                'confidence': conf
                            })
                
                # 更新全局检测结果
                current_detections = detections
                
                # 绘制检测框
                current_frame = draw_boxes(frame, detections)
                
                # 添加统计信息
                cv2.putText(current_frame, f"Detected: {len(detections)} objects", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
                
            except Exception as e:
                print(f"检测过程出错: {e}")
                cv2.putText(current_frame, "Detection Error", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # 编码并返回帧
        try:
            _, buffer = cv2.imencode('.jpg', current_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"编码帧失败: {e}")
            continue
        
        # 控制帧率
        time.sleep(0.033)
    
    # 清理资源
    release_camera()
    print("视频流生成器结束")


@app.route('/detect', methods=['POST'])
def detect_objects():
    """单张图片检测接口"""
    if model is None:
        return jsonify({'error': '模型未加载'}), 500
    if 'image' not in request.files:
        return jsonify({'error': '未上传图片'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '文件名无效'}), 400

    try:
        # 读取图片
        bytes_data = file.read()
        np_array = np.asarray(bytearray(bytes_data), dtype=np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if image is None:
            return jsonify({'error': '图片读取失败'}), 400

        # YOLO检测
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = model(image_rgb)
        detections = []

        if results and len(results) > 0:
            result = results[0]
            if hasattr(result, 'boxes') and result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'label': label,
                        'confidence': conf
                    })

        # 绘制检测框
        result_image = draw_boxes(image, detections)
        _, buffer = cv2.imencode('.jpg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'success': True,
            'detections': detections,
            'result_image': img_base64,
            'detection_count': len(detections)
        })

    except Exception as e:
        print(f"检测过程出错: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/video_feed')
def video_feed():
    """实时视频流接口"""
    global video_stream_active
    
    # 重置标志
    video_stream_active = True
    
    # 返回流式响应
    return Response(generate_video_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/stop_video', methods=['POST'])
def stop_video():
    """停止视频流"""
    global video_stream_active
    
    video_stream_active = False
    
    # 延迟释放摄像头，确保视频流已经结束
    def delayed_release():
        time.sleep(0.5)
        release_camera()
    
    threading.Thread(target=delayed_release).start()
    
    return jsonify({'success': True, 'message': '视频流已停止'})


@app.route('/get_detections', methods=['GET'])
def get_detections():
    """获取最新的检测结果"""
    global current_detections
    return jsonify({
        'success': True,
        'detections': current_detections,
        'detection_count': len(current_detections)
    })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'model_loaded': model is not None,
        'video_active': video_stream_active
    })


@app.route('/camera_check', methods=['GET'])
def camera_check():
    """检查摄像头状态"""
    temp_cap = None
    for i in range(3):
        try:
            temp_cap = cv2.VideoCapture(i)
            if temp_cap.isOpened():
                temp_cap.release()
                return jsonify({
                    'available': True,
                    'index': i,
                    'message': f'摄像头可用 (索引 {i})'
                })
        except:
            pass
    
    return jsonify({
        'available': False,
        'message': '未检测到摄像头'
    })


if __name__ == '__main__':
    app.config['LATEST_DETECTIONS'] = []
    print("=" * 50)
    print("YOLO 物品识别后端服务启动中...")
    print("拍照检测接口: http://localhost:5000/detect")
    print("实时检测接口: http://localhost:5000/video_feed")
    print("=" * 50)
    
    # 检查摄像头
    import requests
    time.sleep(1)
    print("检查摄像头状态...")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

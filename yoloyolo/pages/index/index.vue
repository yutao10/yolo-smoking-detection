<template>
	<view class="container">
		<view class="header">
			<text class="title">YOLO物品识别</text>
			<text class="subtitle">选择拍照或实时检测模式</text>
		</view>

		<!-- 模式切换按钮 -->
		<view class="mode-switch">
			<view class="mode-buttons">
				<button 
					class="mode-btn" 
					:class="{'active': currentMode === 'camera'}"
					@click="switchMode('camera')"
				>
					<text class="mode-icon">📸</text>
					<text>拍照模式</text>
				</button>
				<button 
					class="mode-btn" 
					:class="{'active': currentMode === 'realtime'}"
					@click="switchMode('realtime')"
				>
					<text class="mode-icon">🎥</text>
					<text>实时检测</text>
				</button>
			</view>
		</view>

		<!-- 拍照模式内容 -->
		<view class="camera-mode" v-if="currentMode === 'camera'">
			<!-- 图片预览区域 -->
			<view class="preview-section">
				<view class="image-card" v-if="originalImage">
					<text class="card-title">原始图片</text>
					<image :src="originalImage" mode="aspectFill" class="preview-image" @error="handleImageError"></image>
				</view>

				<view class="image-card" v-if="resultImage">
					<text class="card-title">识别结果 ({{ detectionCount }}个物品)</text>
					<image :src="resultImage" mode="aspectFill" class="preview-image" @error="handleImageError"></image>
				</view>

				<view class="empty-state" v-if="!originalImage && !resultImage">
					<text class="empty-icon">📷</text>
					<text class="empty-text">暂无图片</text>
					<text class="empty-hint">点击下方拍照按钮拍照识别</text>
				</view>
			</view>

			<!-- 检测结果列表 -->
			<view class="results-section" v-if="detections.length > 0">
				<text class="section-title">检测到的物品：</text>
				<view class="results-list">
					<view class="result-item" v-for="(item, index) in detections" :key="index">
						<view class="result-label" :style="{backgroundColor: getColor(index)}">
							{{ item.label }}
						</view>
						<view class="result-confidence">
							置信度: {{ (item.confidence * 100).toFixed(1) }}%
						</view>
					</view>
				</view>
			</view>

			<!-- 拍照模式按钮组 -->
			<view class="button-group">
				<button class="btn btn-primary" @click="takePhoto" :disabled="loading">
					<text class="btn-icon">📸</text>
					<text>拍照识别</text>
				</button>
				
				<button class="btn btn-success" @click="saveToAlbum" v-if="resultImage" :disabled="loading">
					<text class="btn-icon">💾</text>
					<text>保存结果</text>
				</button>
				
				<button class="btn btn-danger" @click="clearAll" v-if="originalImage || resultImage" :disabled="loading">
					<text class="btn-icon">🗑️</text>
					<text>清除</text>
				</button>
			</view>
		</view>

		<!-- 实时检测模式内容 -->
		<view class="realtime-mode" v-if="currentMode === 'realtime'">
			<!-- 视频流区域 -->
			<view class="video-container">
				<image 
					v-if="videoStreamUrl" 
					:src="videoStreamUrl" 
					:key="videoStreamKey"
					class="video-stream"
					mode="aspectFill"
					@error="handleVideoError"
					@load="handleVideoLoad"
				></image>
				<view class="video-placeholder" v-else>
					<text class="placeholder-icon">🎥</text>
					<text class="placeholder-text">{{ videoPlaceholderText }}</text>
				</view>
				
				<!-- 实时检测结果浮层 -->
				<view class="realtime-overlay" v-if="realtimeDetections.length > 0">
					<view class="realtime-stats">
						<text class="stats-text">实时检测到 {{ realtimeDetections.length }} 个物品</text>
					</view>
					<view class="realtime-tags">
						<view class="realtime-tag" v-for="(item, idx) in realtimeDetections.slice(0, 5)" :key="idx">
							{{ item.label }} ({{ (item.confidence * 100).toFixed(0) }}%)
						</view>
					</view>
				</view>
				
				<!-- 加载提示 -->
				<view class="video-loading" v-if="isStarting">
					<view class="loading-spinner-small"></view>
					<text class="loading-text-small">正在启动摄像头...</text>
				</view>
			</view>
			
			<!-- 实时检测模式按钮组 -->
			<view class="realtime-controls">
				<button class="btn-stop" @click="stopRealtimeDetection" v-if="isRealtimeActive">
					<text class="btn-icon">⏹️</text>
					<text>停止检测</text>
				</button>
				<button class="btn-start" @click="startRealtimeDetection" v-else :disabled="isStarting">
					<text class="btn-icon">{{ isStarting ? '⏳' : '🎥' }}</text>
					<text>{{ isStarting ? '启动中...' : '开始实时检测' }}</text>
				</button>
			</view>
			
			<!-- 使用说明 -->
			<view class="realtime-info">
				<text class="info-title">💡 使用说明：</text>
				<text class="info-text">1. 点击"开始实时检测"启动摄像头</text>
				<text class="info-text">2. 系统会自动识别画面中的物品</text>
				<text class="info-text">3. 识别结果会实时显示在画面下方</text>
				<text class="info-text">4. 点击"停止检测"关闭摄像头</text>
			</view>
		</view>

		<!-- 加载提示 -->
		<view class="loading-mask" v-if="loading">
			<view class="loading-content">
				<view class="loading-spinner"></view>
				<text class="loading-text">识别中...</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			// 模式选择
			currentMode: 'camera', // camera: 拍照模式, realtime: 实时检测模式
			
			// 拍照模式数据
			originalImage: '',
			resultImage: '',
			detections: [],
			detectionCount: 0,
			loading: false,
			
			// 实时检测数据
			videoStreamUrl: '',
			videoStreamKey: 0,
			isRealtimeActive: false,
			isStarting: false,
			realtimeDetections: [],
			detectionTimer: null,
			videoPlaceholderText: '正在准备摄像头...',
			
			// 后端服务地址（根据实际情况修改）
			apiUrl: 'http://192.168.220.92:5000'
		}
	},
	
	onLoad() {
		this.checkServerStatus();
	},
	
	onUnload() {
		// 页面卸载时停止实时检测
		if (this.currentMode === 'realtime' && this.isRealtimeActive) {
			this.stopRealtimeDetection();
		}
		this.clearAll();
	},
	
	methods: {
		/**
		 * 获取标签背景色
		 */
		getColor(index) {
			const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'];
			return colors[index % colors.length];
		},
		
		/**
		 * 切换模式
		 */
		switchMode(mode) {
			if (this.currentMode === mode) return;
			
			// 切换模式前清理状态
			if (this.currentMode === 'realtime') {
				this.stopRealtimeDetection();
			} else {
				this.clearAll();
			}
			
			this.currentMode = mode;
		},
		
		/**
		 * 检查后端服务状态
		 */
		checkServerStatus() {
			uni.request({
				url: `${this.apiUrl}/health`,
				method: 'GET',
				timeout: 5000,
				success: (res) => {
					if (res.data?.status === 'ok') {
						console.log('✅ 服务端连接正常');
						uni.showToast({
							title: '服务连接成功',
							icon: 'success',
							duration: 1500
						});
					} else {
						uni.showModal({
							title: '提示',
							content: '服务端响应异常，请检查后端服务',
							showCancel: false
						});
					}
				},
				fail: () => {
					uni.showModal({
						title: '连接失败',
						content: `无法连接到服务器 ${this.apiUrl}，请检查：\n1. 网络是否连通\n2. 后端服务是否启动\n3. IP/端口是否正确`,
						showCancel: false
					});
				}
			});
		},
		
		// ========== 拍照模式方法 ==========
		/**
		 * 拍照
		 */
		takePhoto() {
			uni.chooseImage({
				count: 1,
				sourceType: ['camera'],
				sizeType: ['compressed'],
				success: (res) => {
					const tempFilePath = res.tempFilePaths[0];
					this.originalImage = tempFilePath;
					this.uploadImage(tempFilePath);
				},
				fail: (err) => {
					console.error('拍照失败:', err);
					const errMsg = err.errMsg || '未知错误';
					if (errMsg.includes('auth')) {
						uni.showModal({
							title: '权限不足',
							content: '请在系统设置中开启相机权限后重试',
							showCancel: false
						});
					} else {
						uni.showToast({
							title: '拍照失败：' + errMsg,
							icon: 'none'
						});
					}
				}
			});
		},
		
		/**
		 * 上传图片识别
		 */
		uploadImage(filePath) {
			this.loading = true;
			this.resultImage = '';
			this.detections = [];
			this.detectionCount = 0;
			
			uni.uploadFile({
				url: `${this.apiUrl}/detect`,
				filePath: filePath,
				name: 'image',
				timeout: 30000,
				success: (uploadRes) => {
					try {
						const data = JSON.parse(uploadRes.data);
						if (data.success) {
							this.resultImage = 'data:image/jpeg;base64,' + data.result_image;
							this.detections = data.detections || [];
							this.detectionCount = data.detection_count || 0;
							uni.showToast({
								title: `✅ 识别到${this.detectionCount}个物品`,
								icon: 'success'
							});
						} else {
							uni.showToast({
								title: '识别失败：' + (data.error || '未知错误'),
								icon: 'none'
							});
						}
					} catch (e) {
						console.error('解析失败:', e);
						uni.showToast({
							title: '识别结果解析失败',
							icon: 'none'
						});
					}
				},
				fail: (err) => {
					console.error('上传失败:', err);
					uni.showToast({
						title: '网络错误，请检查服务器连接',
						icon: 'none'
					});
				},
				complete: () => {
					this.loading = false;
				}
			});
		},
		
		/**
		 * 保存图片到相册
		 */
		saveToAlbum() {
			if (!this.resultImage) {
				uni.showToast({
					title: '没有可保存的图片',
					icon: 'none'
				});
				return;
			}
			
			uni.showLoading({
				title: '保存中...',
				mask: true
			});
			
			// #ifdef H5
			try {
				const base64Data = this.resultImage.split(',')[1];
				const byteCharacters = atob(base64Data);
				const byteNumbers = new Array(byteCharacters.length);
				for (let i = 0; i < byteCharacters.length; i++) {
					byteNumbers[i] = byteCharacters.charCodeAt(i);
				}
				const byteArray = new Uint8Array(byteNumbers);
				const blob = new Blob([byteArray], { type: 'image/jpeg' });
				
				const url = URL.createObjectURL(blob);
				const link = document.createElement('a');
				link.href = url;
				link.download = `识别结果_${Date.now()}.jpg`;
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
				URL.revokeObjectURL(url);
				
				uni.hideLoading();
				uni.showToast({
					title: '下载已开始',
					icon: 'success'
				});
			} catch (e) {
				uni.hideLoading();
				window.open(this.resultImage);
				uni.showToast({
					title: '请右键保存图片',
					icon: 'none'
				});
			}
			// #endif
			
			// #ifdef APP-PLUS
			try {
				let base64Data = this.resultImage.split(',')[1];
				let tempFile = `_doc/result_${Date.now()}.jpg`;
				
				let bitmap = new plus.nativeObj.Bitmap();
				bitmap.loadBase64Data(base64Data, () => {
					bitmap.save(tempFile, {}, () => {
						plus.gallery.save(tempFile, () => {
							uni.hideLoading();
							uni.showToast({ title: '保存成功', icon: 'success' });
						}, (err) => {
							uni.hideLoading();
							uni.showToast({ title: '保存失败', icon: 'none' });
						});
					}, (err) => {
						uni.hideLoading();
						uni.showToast({ title: '保存失败', icon: 'none' });
					});
				}, (err) => {
					uni.hideLoading();
					uni.showToast({ title: '图片处理失败', icon: 'none' });
				});
			} catch (e) {
				uni.hideLoading();
				uni.showToast({ title: '保存失败', icon: 'none' });
			}
			// #endif
		},
		
		/**
		 * 清空所有内容
		 */
		clearAll() {
			this.originalImage = '';
			this.resultImage = '';
			this.detections = [];
			this.detectionCount = 0;
			uni.showToast({
				title: '已清空',
				icon: 'success'
			});
		},
		
		/**
		 * 图片加载失败处理
		 */
		handleImageError() {
			uni.showToast({
				title: '图片加载失败',
				icon: 'none'
			});
		},
		
		// ========== 实时检测模式方法 ==========
		/**
		 * 开始实时检测
		 */
		startRealtimeDetection() {
			// #ifdef H5
			if (this.isRealtimeActive || this.isStarting) {
				return;
			}
			
			this.isStarting = true;
			this.videoPlaceholderText = '正在启动摄像头...';
			
			// 先停止之前的检测确保资源释放
			if (this.detectionTimer) {
				clearInterval(this.detectionTimer);
				this.detectionTimer = null;
			}
			
			// 清空之前的视频流URL
			this.videoStreamUrl = '';
			this.realtimeDetections = [];
			
			// 延迟一下再启动，确保资源释放
			setTimeout(() => {
				this.isRealtimeActive = true;
				// 添加时间戳参数避免缓存
				this.videoStreamKey++;
				this.videoStreamUrl = `${this.apiUrl}/video_feed?t=${Date.now()}&key=${this.videoStreamKey}`;
				
				// 定时获取检测结果
				this.detectionTimer = setInterval(() => {
					this.fetchLatestDetections();
				}, 500);
				
				setTimeout(() => {
					this.isStarting = false;
					uni.showToast({
						title: '实时检测已启动',
						icon: 'success',
						duration: 1500
					});
				}, 500);
			}, 300);
			// #endif
			
			// #ifndef H5
			uni.showModal({
				title: '提示',
				content: '实时检测功能目前仅在浏览器（H5）环境下支持，请使用浏览器打开此页面',
				showCancel: false
			});
			// #endif
		},
		
		/**
		 * 获取最新检测结果
		 */
		fetchLatestDetections() {
			if (!this.isRealtimeActive) return;
			
			uni.request({
				url: `${this.apiUrl}/get_detections`,
				method: 'GET',
				timeout: 3000,
				success: (res) => {
					if (res.data && res.data.success && this.isRealtimeActive) {
						this.realtimeDetections = res.data.detections || [];
					}
				},
				fail: (err) => {
					console.error('获取检测结果失败:', err);
				}
			});
		},
		
		/**
		 * 停止实时检测
		 */
		stopRealtimeDetection() {
			this.isRealtimeActive = false;
			this.isStarting = false;
			
			// 停止定时器
			if (this.detectionTimer) {
				clearInterval(this.detectionTimer);
				this.detectionTimer = null;
			}
			
			// 发送停止请求
			uni.request({
				url: `${this.apiUrl}/stop_video`,
				method: 'POST',
				timeout: 5000,
				success: (res) => {
					console.log('停止成功:', res);
				},
				fail: (err) => {
					console.error('停止失败:', err);
				},
				complete: () => {
					// 清空视频流URL和检测结果
					this.videoStreamUrl = '';
					this.realtimeDetections = [];
					this.videoPlaceholderText = '摄像头已关闭';
					
					uni.showToast({
						title: '实时检测已停止',
						icon: 'success',
						duration: 1500
					});
					
					// 延迟重置占位文字
					setTimeout(() => {
						if (!this.isRealtimeActive) {
							this.videoPlaceholderText = '点击开始检测启动摄像头';
						}
					}, 2000);
				}
			});
		},
		
		/**
		 * 视频加载错误处理
		 */
		handleVideoError(e) {
			console.error('视频加载错误:', e);
			if (this.isRealtimeActive) {
				uni.showToast({
					title: '视频流加载失败，请重试',
					icon: 'none'
				});
				this.stopRealtimeDetection();
			}
		},
		
		/**
		 * 视频加载成功处理
		 */
		handleVideoLoad() {
			console.log('视频加载成功');
			this.videoPlaceholderText = '';
		}
	}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	padding: 20rpx;
	box-sizing: border-box;
}

.header {
	text-align: center;
	padding: 30rpx 0 20rpx;
}

.title {
	font-size: 44rpx;
	font-weight: bold;
	color: #fff;
	display: block;
}

.subtitle {
	font-size: 24rpx;
	color: rgba(255,255,255,0.8);
	display: block;
	margin-top: 8rpx;
}

/* 模式切换按钮 */
.mode-switch {
	padding: 20rpx 0;
}

.mode-buttons {
	display: flex;
	flex-direction: row;
	gap: 20rpx;
	padding: 0 20rpx;
}

.mode-btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 80rpx;
	background: rgba(255,255,255,0.2);
	border-radius: 40rpx;
	font-size: 28rpx;
	color: #fff;
	border: none;
}

.mode-btn.active {
	background: #fff;
	color: #667eea;
	box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.15);
}

.mode-icon {
	margin-right: 10rpx;
	font-size: 32rpx;
}

/* 拍照模式样式 */
.camera-mode {
	margin-top: 20rpx;
}

.preview-section {
	background: #fff;
	border-radius: 20rpx;
	padding: 30rpx;
	margin: 20rpx 0;
	box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.1);
}

.image-card {
	margin-bottom: 0;
}

.card-title {
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
	display: block;
	margin-bottom: 15rpx;
}

.preview-image {
	width: 100%;
	height: 400rpx;
	border-radius: 12rpx;
	background: #f5f5f5;
}

.empty-state {
	text-align: center;
	padding: 80rpx 0;
}

.empty-icon {
	font-size: 100rpx;
	display: block;
}

.empty-text {
	font-size: 32rpx;
	color: #999;
	display: block;
	margin-top: 20rpx;
}

.empty-hint {
	font-size: 26rpx;
	color: #ccc;
	display: block;
	margin-top: 10rpx;
}

.results-section {
	background: #fff;
	border-radius: 20rpx;
	padding: 30rpx;
	margin: 20rpx 0;
	box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}

.section-title {
	font-size: 32rpx;
	font-weight: bold;
	color: #333;
	display: block;
	margin-bottom: 20rpx;
}

.results-list {
	display: flex;
	flex-wrap: wrap;
	gap: 15rpx;
}

.result-item {
	display: inline-flex;
	align-items: center;
	padding: 10rpx 20rpx;
	background: #f8f9fa;
	border-radius: 40rpx;
}

.result-label {
	padding: 8rpx 16rpx;
	border-radius: 30rpx;
	color: #fff;
	font-size: 24rpx;
	font-weight: bold;
	margin-right: 10rpx;
}

.result-confidence {
	font-size: 24rpx;
	color: #666;
}

.button-group {
	display: flex;
	flex-direction: row;
	gap: 20rpx;
	margin: 30rpx 0;
	justify-content: center;
}

.btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 88rpx;
	border-radius: 44rpx;
	font-size: 28rpx;
	border: none;
}

.btn:disabled {
	opacity: 0.6;
}

.btn-icon {
	margin-right: 8rpx;
	font-size: 32rpx;
}

.btn-primary {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	color: #fff;
}

.btn-success {
	background: linear-gradient(135deg, #4CAF50, #45a049);
	color: #fff;
}

.btn-danger {
	background: linear-gradient(135deg, #f44336, #d32f2f);
	color: #fff;
}

/* 实时检测模式样式 */
.realtime-mode {
	margin-top: 20rpx;
}

.video-container {
	position: relative;
	background: #000;
	border-radius: 20rpx;
	overflow: hidden;
	margin: 20rpx 0;
	min-height: 500rpx;
}

.video-stream {
	width: 100%;
	height: 500rpx;
	object-fit: cover;
}

.video-placeholder {
	width: 100%;
	height: 500rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	background: #1a1a1a;
}

.placeholder-icon {
	font-size: 80rpx;
}

.placeholder-text {
	color: #666;
	margin-top: 20rpx;
	font-size: 28rpx;
}

.video-loading {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0,0,0,0.7);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	z-index: 10;
}

.loading-spinner-small {
	width: 50rpx;
	height: 50rpx;
	border: 3rpx solid rgba(255,255,255,0.3);
	border-top: 3rpx solid #fff;
	border-radius: 50%;
	animation: spin 1s linear infinite;
	margin-bottom: 15rpx;
}

.loading-text-small {
	color: #fff;
	font-size: 24rpx;
}

.realtime-overlay {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	background: linear-gradient(transparent, rgba(0,0,0,0.8));
	padding: 30rpx 20rpx 20rpx;
}

.realtime-stats {
	margin-bottom: 15rpx;
}

.stats-text {
	color: #fff;
	font-size: 24rpx;
	background: rgba(0,0,0,0.5);
	padding: 6rpx 12rpx;
	border-radius: 20rpx;
}

.realtime-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 10rpx;
}

.realtime-tag {
	background: rgba(102, 126, 234, 0.9);
	color: #fff;
	padding: 6rpx 16rpx;
	border-radius: 30rpx;
	font-size: 22rpx;
}

.realtime-controls {
	padding: 20rpx;
	margin: 20rpx 0;
}

.btn-stop, .btn-start {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 88rpx;
	border-radius: 44rpx;
	font-size: 32rpx;
	border: none;
	color: #fff;
	width: 100%;
}

.btn-stop {
	background: linear-gradient(135deg, #f44336, #d32f2f);
}

.btn-start {
	background: linear-gradient(135deg, #4CAF50, #45a049);
}

.btn-start:disabled {
	opacity: 0.6;
}

.realtime-info {
	background: rgba(255,255,255,0.95);
	border-radius: 20rpx;
	padding: 30rpx;
	margin: 20rpx 0;
}

.info-title {
	font-size: 28rpx;
	font-weight: bold;
	color: #333;
	display: block;
	margin-bottom: 15rpx;
}

.info-text {
	font-size: 24rpx;
	color: #666;
	display: block;
	margin-top: 10rpx;
	line-height: 1.6;
}

/* 加载遮罩 */
.loading-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0,0,0,0.7);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}

.loading-content {
	background: #fff;
	padding: 40rpx;
	border-radius: 20rpx;
	text-align: center;
}

.loading-spinner {
	width: 60rpx;
	height: 60rpx;
	border: 4rpx solid #f3f3f3;
	border-top: 4rpx solid #667eea;
	border-radius: 50%;
	animation: spin 1s linear infinite;
	margin: 0 auto 20rpx;
}

@keyframes spin {
	0% { transform: rotate(0deg); }
	100% { transform: rotate(360deg); }
}

.loading-text {
	font-size: 28rpx;
	color: #666;
}
</style>
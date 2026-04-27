# YOLO11 菌落检测训练 - 启智平台配置

## 数据集上传

### 1. 上传数据集到启智平台
```bash
# 数据集位置（本地）
G:/train/yolo11_fase_v2/        # 小数据集（2352张）
G:/train/yolo11_new_colony/     # 大数据集（11030张）

# 压缩数据集
cd G:/train
7z a yolo11_fase_v2.zip yolo11_fase_v2/
7z a yolo11_new_colony.zip yolo11_new_colony/

# 上传到启智平台数据集管理
# 网址: https://openi.pcl.ac.cn/datasets
```

### 2. 创建训练任务

**仓库**: bhys/MIC-all  
**分支**: yolo11-training  
**启动文件**: train_yolo11_openi.py  
**数据集**: 选择上传的数据集（yolo11_fase_v2 或 yolo11_new_colony）

### 3. 环境配置

**镜像**: PyTorch 2.0+ (CUDA 11.8+)  
**资源**: 
- GPU: NVIDIA V100 32GB（推荐）
- CPU: 8核
- 内存: 32GB

**环境变量**:
```bash
OPENI_DATASET_PATH=/cache/dataset  # 启智平台会自动挂载
```

### 4. 依赖安装

在启动脚本前添加：
```bash
pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 训练参数说明

### 小数据集（fase_v2）
- 图像数: 2,352张
- 类别: 5个
- 预计训练时间: 2-3小时（V100）
- 目标: 快速验证YOLO11效果

### 大数据集（new_colony）
- 图像数: 11,030张
- 类别: 7个（包含污染检测）
- 预计训练时间: 8-10小时（V100）
- 目标: 生产级模型

---

## 训练后操作

### 1. 下载模型
```bash
# 最佳模型位置
runs/colony_detection/yolo11n_colony/weights/best.pt
runs/colony_detection/yolo11n_colony/weights/best.onnx
```

### 2. 本地测试
```bash
# 下载到本地后
python scripts/test_inference_speed.py --model best.onnx
```

### 3. 部署到树莓派
```bash
# 通过PowerShell传输
scp -i ".ssh/id_ed25519" best.onnx bhys@192.168.11.239:~/CNN-MicroAI-Colony/onnx_model/
```

---

## 故障排查

### 问题1: 找不到数据集
**解决**: 检查环境变量 `OPENI_DATASET_PATH`，确保数据集已挂载

### 问题2: GPU内存不足
**解决**: 减小batch size（16 -> 8）

### 问题3: 训练过慢
**解决**: 使用更小的数据集（fase_v2）先验证

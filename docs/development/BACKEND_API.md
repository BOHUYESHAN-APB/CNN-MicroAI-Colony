# 后端 API 文档

## 基本信息

- 基础URL: `http://localhost:8000`
- 所有响应格式均为JSON
- 图片上传使用multipart/form-data格式

## API 端点

### 1. 状态检查

```
GET /
```

返回后端服务状态。

**响应示例:**
```json
{
    "message": "Colony Analysis Backend is running"
}
```

### 2. 图像分析

```
POST /analyze
```

分析单张图片中的菌落。

**参数:**
- `file`: 图片文件 (multipart/form-data)

**响应示例:**
```json
{
    "status": "success",
    "filename": "example.jpg",
    "results": {
        "count": 10,
        "colonies": [
            {
                "position": [100, 100],
                "size": 15,
                "confidence": 0.95
            }
        ],
        "tilt": [0.5, 0.3]
    }
}
```

### 3. 相机校准

```
POST /calibrate
```

进行相机校准。

**参数:**
- `file`: 校准图片 (multipart/form-data)

**响应示例:**
```json
{
    "status": "success",
    "message": "Camera calibration completed"
}
```

### 4. 系统设置

```
GET /settings
```

获取系统设置。

**响应示例:**
```json
{
    "camera": {
        "resolution": "1920x1080",
        "fps": 30
    },
    "analysis": {
        "confidence_threshold": 0.5,
        "min_colony_size": 10
    }
}
```

## 错误处理

所有API在发生错误时返回相应的HTTP状态码和错误信息。

**错误响应示例:**
```json
{
    "status": "error",
    "message": "错误描述"
}
```

常见HTTP状态码：
- 400: 错误的请求参数
- 404: 资源不存在
- 500: 服务器内部错误

## WebSocket API

### 1. 实时相机预览

```
WS /ws/camera
```

获取实时相机预览数据流。

**消息格式:**
```json
{
    "type": "frame",
    "data": "base64编码的图像数据",
    "timestamp": 1234567890,
    "tilt": {
        "x": 0.5,
        "y": 0.3
    }
}
```

### 2. 分析结果推送

```
WS /ws/analysis
```

接收实时分析结果。

**消息格式:**
```json
{
    "type": "analysis_result",
    "timestamp": 1234567890,
    "data": {
        "count": 10,
        "colonies": [
            {
                "position": [100, 100],
                "size": 15,
                "confidence": 0.95
            }
        ]
    }
}
```

## 文件格式

### 1. 工程文件结构

工程文件采用文件夹形式组织(.colony后缀)，包含以下内容：

```
project_name.colony/
├── source/                   # 原始图像
├── analysis/                # 分析结果
└── project.json            # 工程配置
```

### 2. 分析结果格式

```json
{
    "image_id": "img_001",
    "timestamp": "2025-04-30T10:00:00Z",
    "results": {
        "count": 10,
        "colonies": [
            {
                "position": [100, 100],
                "size": 15,
                "confidence": 0.95
            }
        ],
        "metadata": {
            "camera_tilt": [0.5, 0.3],
            "scale": 1.0
        }
    }
}
```

## 开发说明

1. 所有坐标以图像左上角为原点(0,0)
2. 角度采用度数表示，范围：-180° ~ 180°
3. 置信度范围：0.0 ~ 1.0
4. 时间戳采用ISO 8601格式

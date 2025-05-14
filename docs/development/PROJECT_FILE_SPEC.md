# 工程文件规范

## 概述

工程文件采用文件夹形式组织，使用 `.colony` 扩展名标识工程文件夹。每个工程包含源图像、分析结果和配置信息。

## 工程文件结构

```
project_name.colony/           # 工程文件夹
├── source/                   # 原始图像目录
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── analysis/                # 分析结果目录
│   ├── image1_result.json   # 每个图像的分析结果
│   ├── image2_result.json
│   └── ...
└── project.json            # 工程配置文件
```

## 配置文件格式 (project.json)

```json
{
    "project": {
        "id": "unique_project_id",
        "name": "项目名称",
        "created_at": "2025-04-30T10:00:00Z",
        "updated_at": "2025-04-30T10:30:00Z",
        "version": "2.0.0"
    },
    "settings": {
        "analysis": {
            "model": {
                "type": "faster_rcnn",
                "version": "v1.0",
                "parameters": {
                    "confidence_threshold": 0.5,
                    "nms_threshold": 0.3
                }
            },
            "preprocessing": {
                "enabled": [
                    "grayscale",
                    "gaussian_blur"
                ],
                "parameters": {
                    "gaussian_blur": {
                        "kernel_size": 3
                    }
                }
            }
        },
        "export": {
            "formats": ["json", "csv", "pdf"],
            "include_images": true,
            "include_analytics": true
        }
    },
    "files": {
        "images": [
            {
                "id": "img_001",
                "filename": "image1.jpg",
                "path": "source/image1.jpg",
                "analysis_result": "analysis/image1_result.json",
                "created_at": "2025-04-30T10:05:00Z",
                "metadata": {
                    "width": 1920,
                    "height": 1080,
                    "format": "JPEG"
                }
            }
        ]
    },
    "analysis_results": {
        "summary": {
            "total_images": 1,
            "total_colonies": 0,
            "average_confidence": 0.0
        }
    }
}
```

## 分析结果格式 (image_result.json)

```json
{
    "image_id": "img_001",
    "filename": "image1.jpg",
    "analysis_time": "2025-04-30T10:05:30Z",
    "model_info": {
        "type": "faster_rcnn",
        "version": "v1.0"
    },
    "results": {
        "colonies": [
            {
                "id": 1,
                "bbox": [100, 100, 150, 150],
                "confidence": 0.95,
                "size": 45,
                "color": [128, 128, 128]
            }
        ],
        "statistics": {
            "total_count": 1,
            "average_size": 45.0,
            "density": 0.001
        }
    },
    "preprocessing": {
        "steps": ["grayscale", "gaussian_blur"],
        "parameters": {
            "gaussian_blur": {
                "kernel_size": 3
            }
        }
    }
}
```

## 使用指南

### 创建新工程

1. 在目标目录创建 `.colony` 后缀的文件夹
2. 创建必要的子目录（source, analysis）
3. 生成初始的 project.json 文件

### 导入图像

1. 将图像文件复制到 `source` 目录
2. 更新 project.json 中的文件列表
3. 生成对应的分析结果文件

### 导出数据

支持以下导出格式：
- JSON：完整的分析数据
- CSV：基础的统计数据
- Excel：详细的表格数据
- PDF：报告格式（包含图片和分析）
- Markdown：纯文本报告

### 工程文件管理

- 工程文件可以打包为zip格式进行传输
- 支持工程文件的导入导出
- 支持多个工程的批量处理

## 注意事项

1. 文件命名规范
   - 使用小写字母
   - 避免特殊字符
   - 使用下划线连接单词

2. 数据完整性
   - 定期备份工程文件
   - 保持文件结构完整
   - 避免手动修改JSON文件

3. 版本兼容
   - 向后兼容旧版本格式
   - 版本号遵循语义化版本规范
   - 提供版本转换工具

## 最佳实践

1. 工程组织
   - 按日期或实验批次组织工程
   - 使用有意义的工程名称
   - 保持文件结构清晰

2. 数据管理
   - 定期清理无用数据
   - 及时更新分析结果
   - 保持元数据完整性

3. 协作开发
   - 遵循统一的命名规范
   - 保持文件结构一致
   - 做好版本控制

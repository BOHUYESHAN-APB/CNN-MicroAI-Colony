# 树莓派单摄像头 MVP 架构（CTk + Python）

## 目标范围（当前阶段）

- 单可见光摄像头实时预览
- 拍照并保存到本地项目目录
- 导入图片（含 USB 挂载目录导入）
- 本地 ONNX 推理、标注图保存、基础结果记录
- 置信度两级分类标注（A/B）与多颜色框选
- 批次 CSV 报表导出与 ZIP 打包导出
- 一键打开 3D HTML 演示页面

## 分层设计

```text
CTk UI (apps/pi_ctk/ui/app.py)
  -> CameraService (core/camera_service.py)
  -> InferenceService (core/inference_service.py)
  -> StorageService (core/storage_service.py)
  -> DemoService (core/demo_service.py)
```

- UI 层只做展示与用户交互，不直接写推理细节。
- 推理和 IO 使用后台线程，避免阻塞 UI 主线程。
- 结果落地为文件 + JSONL 历史，便于后续扩展时序分析。

## 目录与数据约定

- 默认数据根目录：`~/.cnn_microai_pi/`
- 子目录：
  - `captures/` 拍照原图
  - `imports/` 导入原图
  - `results/` 标注图
  - `history/history.jsonl` 推理记录

历史记录字段建议：

- `timestamp`
- `source_type` (`capture` / `import` / `preview`)
- `source_path`
- `annotated_path`
- `model_path`
- `score_threshold`
- `nms_iou`
- `count`
- `high_count`
- `low_count`
- `avg_latency_ms`
- `top_score`
- `avg_score`
- `summary_text`

## 线程模型

- UI 主线程：窗口、预览刷新、按钮交互。
- 推理线程：模型加载/推理/后处理。
- 预览刷新：`after()` 定时读取最新帧，保持界面流畅。

## 设备与扩展策略

- 当前只实现 `camera_index=0` 的单摄像头链路。
- 未来多光谱扩展：增加 `camera_id`、`spectrum_band` 字段并在 UI 中支持多路选择。
- 未来板级迁移：服务层与 UI 分离，便于替换硬件驱动层。

## 与现有仓库的衔接

- 预处理与输出约定沿用 `scripts/pi_infer_onnx.py`：
  - 输入 `800x800`
  - `mean/std` 归一化
  - 输出 `boxes/labels/scores/num_detections`
- 可直接复用已有 ONNX 模型：`onnx model/checkpoint_epoch_31.onnx`
- 3D 演示可通过配置路径指向你现有 `model-output2.html`

## 下一阶段建议

- 增加批次/时间点管理（同一样本多时刻观测）
- 增加 CSV/PDF 导出
- 增加本地 FastAPI（可选）给 Web 端或上位机调用

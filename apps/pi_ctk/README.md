# Raspberry Pi CTk MVP

单摄像头可见光阶段的本地工程版 MVP，包含：

- 实时预览
- 拍照推理
- 图片导入推理
- USB 目录导入（自动拷贝到本地）
- ONNX 推理 + 标注图保存（图片右侧自动生成文字报告区）
- 两级框选分类（A:高置信度, B:常规置信度）与不同颜色标注
- 历史记录（JSONL，按菌种/批次）
- 批次 CSV 统计导出 + 全量 ZIP 打包导出
- 3D HTML 演示入口

## 运行

```bash
pip install -r apps/pi_ctk/requirements.txt
python -m apps.pi_ctk.main
```

## 默认路径

- 模型：`onnx model/checkpoint_epoch_31.onnx`
- 3D演示：优先 `D:\-Users-\Documents\GitHub\model-\model-output2.html`
- 数据目录：`~/.cnn_microai_pi/`

## 数据目录结构

```text
~/.cnn_microai_pi/
  batches/
    <strain_name>/
      <batch_id>/
        captures/
        imports/
        results/
        history/history.jsonl
        exports/
```

## 命名规范（可配置）

- 文件名格式：`<PREFIX>_<strain>_<batch>_<timefmt>_<ms>.<ext>`
- 默认：
  - RAW 原图：`RAW_xxx.jpg`
  - IMP 导入图：`IMP_xxx.jpg`
  - ANN 标注图：`ANN_xxx.jpg`
  - REPORT 报表：`REPORT_xxx.csv`

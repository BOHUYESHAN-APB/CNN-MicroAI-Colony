# MMDetection 模型转换说明

概述：

我们尝试把训练产物 `d:\train\faster_rcnn_colony_epoch12.pth` 转换为 ONNX。因为该模型最初使用 MMDetection / mmcv 框架训练，仓库内没有相应的完整 MMDetection 配置文件（`configs/...`），所以我们采用了启发式 state_dict 映射方法把权重映射到 torchvision Faster R-CNN，并导出了一个 ONNX（位于 `onnx model/faster_rcnn_colony_epoch12.onnx`）。

问题与限制：
- 启发式映射并非 100% 保证匹配：部分参数可能未被正确映射或命名差异导致行为偏差。脚本输出显示匹配率为例如 288 / 295（视 checkpoint 而定）。
- MMDetection 的训练配置包含关键预处理、anchor 设置、ROI heads 配置等，这些都会影响检测行为；缺失原始 config 会导致导出模型与训练模型不完全一致。
- 在加载 checkpoint 时遇到 `weights_only` / safe globals 的安全加载限制，需要额外的处理以安全恢复权重。

建议的下一步：
1. 如果你仍有原训练时使用的 MMDetection config（通常位于 `configs/...`），请把它一并提供，我们可以用 mmdet 的官方导出流程重新生成 ONNX，保证更高的保真度。  
2. 如果没有配置，考虑重训练（或微调）基于 torchvision 的 Faster R-CNN，以便得到更可控、可导出的 checkpoint（如 `checkpoint_epoch_31.pth` 所示，这个版本导出和量化效果较好）。

已完成操作：
- 生成了启发式映射并导出 ONNX：`onnx model/faster_rcnn_colony_epoch12.onnx`  
- 在 `scripts/` 下保留了映射与导出脚本（`export_mmdet_and_test.py`），便于未来复用或改进映射策略。

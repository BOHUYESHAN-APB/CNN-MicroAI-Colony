# AI 编程步骤记录

## 操作记录

### 1. 创建新目录结构
- 新建 `models-train/in-use/old` 和 `models-train/in-use/last` 文件夹。
- 将原有的 `faster_rcnn_resnet50` 和 `main_models_train` 训练脚本迁移到 `old` 文件夹下。

### 2. 汇总优秀点
- 结合 `faster_rcnn_resnet50` 的轻量化和 `main_models_train` 的模块化特点，编写了新的训练脚本 `combined_model_train.py`。
- 新脚本存放于 `models-train/in-use/last` 文件夹中。

### 3. 创建 documents 文件夹
- 按照现有 `docs` 目录的结构创建文件夹，但不迁移 `docs` 中的文件。
- 新建 `data-change.md` 文件记录操作步骤。
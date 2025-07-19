#!/bin/bash

# 批量运行所有模型的训练脚本
# 包括 models-train/in-use/last 和 models-train/comparison 中的模型

echo "开始批量运行所有模型训练..."

# 定义模型路径
LAST_MODELS_PATH="models-train/in-use/last"
COMPARISON_MODELS_PATH="models-train/comparison"

# 运行 last 目录中的模型
echo "运行 last 目录中的模型..."
for model_dir in "$LAST_MODELS_PATH"/*; do
    if [ -d "$model_dir" ] && [ -f "$model_dir/src/train.py" ]; then
        echo "运行模型: $model_dir"
        python "$model_dir/src/train.py"
    fi
done

# 运行 comparison 目录中的模型
echo "运行 comparison 目录中的模型..."
for model_dir in "$COMPARISON_MODELS_PATH"/*; do
    if [ -d "$model_dir" ] && [ -f "$model_dir/src/train.py" ]; then
        echo "运行模型: $model_dir"
        python "$model_dir/src/train.py"
    fi
done

echo "所有模型训练完成！"
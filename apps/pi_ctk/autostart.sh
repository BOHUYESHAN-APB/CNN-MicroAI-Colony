#!/bin/bash
# MicroAI Colony Counter 开机自启动脚本
# 安装方法：
# 1. chmod +x autostart.sh
# 2. 编辑 ~/.config/autostart/microai-colony.desktop

# 等待系统完全启动
sleep 5

# 激活虚拟环境（如果使用）
# source /path/to/venv/bin/activate

# 启动应用（全屏模式）
cd "$(dirname "$0")/../.."
python -m apps.pi_ctk.main

# 如果应用崩溃，等待10秒后重启
while true; do
    sleep 10
    python -m apps.pi_ctk.main
done

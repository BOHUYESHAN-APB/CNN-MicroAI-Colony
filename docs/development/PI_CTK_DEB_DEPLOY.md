# Pi CTk .deb 部署指南

> 本文件恢复自交接文档 §11 (Pi 打包/部署)，已适配当前 PyTorch/ORT 技术栈。
> 与交接文档的关系：交接文档提到的 `docs/development/PI_CTK_DEB_DEPLOY.md` 在当前仓库中不存在，本文档为重建版本。

## 概述

将 `apps/pi_ctk/` 打包为 `.deb` 并部署到 Raspberry Pi ARM64。

## 前提条件

- **构建端** (开发机): Python 3.9+, `dpkg-deb` (Windows 需 WSL 或 Docker)
- **目标端** (Pi): Raspberry Pi 4, Ubuntu 22.04 ARM64, Python 3.9+
- **网络**: 开发机与 Pi 在同一局域网

## 快速开始

### 1. 构建 .deb

```bash
python scripts/build_pi_ctk_deb.py --version 0.1.0
```

输出: `dist/cnn-microai-pi_0.1.0_arm64.deb`

### 2. 手动安装到 Pi

```bash
# 上传
scp dist/cnn-microai-pi_0.1.0_arm64.deb pi@192.168.11.239:/tmp/

# SSH 到 Pi 并安装
ssh pi@192.168.11.239
sudo dpkg -i /tmp/cnn-microai-pi_0.1.0_arm64.deb
sudo apt-get install -f -y  # 如果依赖缺失
```

### 3. 一键构建+部署

```bash
python scripts/build_pi_ctk_deb.py --version 0.1.0 \
  --host 192.168.11.239 --user pi --install
```

### 4. 运行

```bash
# 在 Pi 上
cnn-microai-pi
```

## .deb 包结构

```
cnn-microai-pi_0.1.0_arm64.deb
├── opt/cnn-microai-pi/           # 应用代码
│   ├── core/                     # 推理、存储、摄像头服务
│   ├── ui/                       # CTk 界面
│   ├── main.py                   # 入口
│   ├── requirements.txt          # Python 依赖
│   └── onnx_model/               # ONNX 模型文件
├── usr/local/bin/cnn-microai-pi  # 启动脚本
└── DEBIAN/
    ├── control                   # 包元数据
    └── postinst                  # 安装后自动创建 venv + pip install
```

## 安装后验证

```bash
# 检查包状态
dpkg -s cnn-microai-pi

# 检查安装目录
ls /opt/cnn-microai-pi/

# 测试运行
cnn-microai-pi
```

## 常见问题

### dpkg 架构不匹配
Pi 上如果报 "architecture arm64 does not match system"：
```bash
sudo dpkg --add-architecture arm64  # 通常不需要，Pi 原生就是 arm64
```

### 依赖安装失败
```bash
sudo apt-get install -f -y
cd /opt/cnn-microai-pi
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### ONNX Runtime 安装慢
```bash
# 使用国内源
.venv/bin/pip install onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 与其他脚本的关系

| 脚本 | 用途 |
|---|---|
| `scripts/build_pi_ctk_deb.py` | 构建 .deb + 可选远程部署 |
| `scripts/pi_remote_deploy_and_test.py` | SSH 部署 ONNX + 运行推理测试 (不用 .deb) |
| `scripts/pi_remote_count_benchmark.py` | Pi 延迟基准测试 |
| `scripts/run_count_compare_pipeline.py` | 多模型对比编排 |

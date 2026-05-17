# 树莓派UI现代化功能说明

## 新增功能

### 1. 仪器化界面
- **全屏模式**：按 `F11` 切换全屏，按 `ESC` 退出
- **状态指示灯**：实时显示相机和模型状态（绿色=正常，红色=异常）
- **专业标题栏**：显示系统名称和功能按钮

### 2. 模型切换
- **基础模型**：5类菌落检测（开源版）
- **高级模型**：7类菌落检测，包含污染检测（商业版）
- 一键切换，重载模型即可生效

### 3. 设置面板
- 开机自启动配置
- 全屏模式配置
- 快捷键提示

### 4. GitHub反馈集成
- 点击"💬 反馈"按钮直接跳转到GitHub Issues
- 自动打开浏览器，方便用户提交问题

### 5. 关于页面
- 显示版本信息、开源协议
- 功能特性列表
- 快捷键说明
- GitHub仓库链接

---

## 开机自启动配置

### 方法1：systemd服务（推荐）

```bash
# 1. 复制服务文件
sudo cp apps/pi_ctk/microai-colony.service /etc/systemd/system/

# 2. 修改服务文件中的路径
sudo nano /etc/systemd/system/microai-colony.service
# 将 WorkingDirectory 改为实际项目路径

# 3. 启用服务
sudo systemctl enable microai-colony.service
sudo systemctl start microai-colony.service

# 4. 查看状态
sudo systemctl status microai-colony.service

# 5. 停止服务
sudo systemctl stop microai-colony.service

# 6. 禁用自启动
sudo systemctl disable microai-colony.service
```

### 方法2：桌面自启动

```bash
# 1. 创建自启动目录
mkdir -p ~/.config/autostart

# 2. 创建桌面文件
cat > ~/.config/autostart/microai-colony.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=MicroAI Colony Counter
Exec=/home/pi/CNN-MicroAI-Colony/apps/pi_ctk/autostart.sh
Terminal=false
Hidden=false
EOF

# 3. 赋予执行权限
chmod +x apps/pi_ctk/autostart.sh
```

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F11` | 切换全屏模式 |
| `ESC` | 退出全屏模式 |

---

## 商业版与开源版差异

### 开源版（基础模型）
- ✅ 菌落计数（5类）
- ✅ 抑菌圈检测
- ✅ 蓝白斑检测
- ✅ 数据导出
- ✅ 完整UI功能

### 商业版（高级模型）
- ✅ 所有开源功能
- ✅ **污染检测**（Contamination类别）
- ✅ **缺陷检测**（Defect类别）
- ✅ 更高精度（大数据集训练）
- ✅ 技术支持与定制服务

**模型文件：**
- 开源：`checkpoint_epoch_31.onnx`（5类）
- 商业：`checkpoint_advanced.onnx`（7类，需授权）

---

## 界面预览

```
┌─────────────────────────────────────────────────────────────┐
│ ● 相机  ● 模型    MicroAI Colony Counter    [基础|高级] ⚙ 💬 ℹ │
├─────────────────────────────────────────────────────────────┤
│                                              │               │
│                                              │  模型路径     │
│         相机预览区域                          │  [________]   │
│                                              │               │
│                                              │  检测参数     │
│                                              │  Score NMS A  │
│                                              │               │
│  [拍照] [导入] [USB批量] [刷新]               │  命名规范     │
│                                              │  菌种 批次    │
│                                              │               │
│                                              │  [重载][3D][导出]│
│                                              │               │
│                                              │  历史记录     │
│                                              │  [________]   │
└─────────────────────────────────────────────────────────────┘
```

---

## 故障排查

### 问题1：自启动失败
**解决**：检查服务日志
```bash
sudo journalctl -u microai-colony.service -f
```

### 问题2：全屏模式无法退出
**解决**：按 `ESC` 键或 `Alt+F4` 关闭窗口

### 问题3：模型切换后无效
**解决**：切换模型后，点击"重载模型"按钮

---

## GitHub仓库

https://github.com/BOHUYESHAN-APB/CNN-MicroAI-Colony

**反馈问题：** https://github.com/BOHUYESHAN-APB/CNN-MicroAI-Colony/issues

# 菌落检测分析系统

## 项目说明
基于深度学习的微生物菌落检测与计数系统，支持多种培养基类型和成像条件，提供精确的菌落计数和分析功能。

## 目录结构
```
CNN-/
├── app/                    # 应用程序主目录
│   ├── config/            # 配置文件
│   ├── database/          # 数据库管理
│   ├── font/             # 字体资源
│   ├── gui/              # 图形界面
│   ├── models/           # 模型定义
│   ├── resources/        # 资源文件
│   │   └── i18n/        # 国际化文件
│   ├── templates/        # 报告模板
│   └── utils/           # 工具函数
├── checkpoints/          # 模型检查点
├── docs/                 # 文档目录
├── pic/                  # 示例图片
│   ├── higher-resolution/
│   └── lower-resolution/
├── scripts/             # 维护脚本
└── src/                 # 源代码
    ├── data/           # 数据处理
    ├── models/         # 模型实现
    └── ops/            # 算子实现
```

## 技术栈
- **深度学习框架**: PyTorch 1.9+
- **图像处理**: OpenCV 4.5+
- **GUI框架**: PyQt5
- **数据处理**: NumPy, Pandas
- **可视化**: Matplotlib
- **国际化**: Qt Linguist

## 功能状态

### 已完成功能
- [x] 基础图像分析功能
  - 单图分析
  - 多图批量分析
  - 菌落计数与统计
- [x] 结果可视化
  - 分布直方图
  - 计数序列图
  - 置信度分布图
  - 多图对比图表
- [x] 数据导出
  - CSV格式导出
  - Excel格式导出（含统计信息）
  - JSON格式导出
  - 图表导出（PNG/PDF）
- [x] 界面功能
  - 文件选择对话框导入
  - 图像列表管理
  - 结果预览
  - 国际化支持（中英文）

### 待完成功能
- [ ] 高级分析功能
  - 菌种分类
  - 生长曲线分析
  - 药敏测试分析
- [ ] 界面优化
  - Fluent Design迁移
  - 深色模式支持
  - 拖放操作支持
- [ ] 数据管理
  - 本地数据库存储
  - 历史记录管理
  - 批量导入导出

## 安装说明

### 系统要求
- Windows 10/11 (64位)
- Python 3.8+
- CUDA 11.0+ (可选，用于GPU加速)
- 8GB+ RAM
- 500MB 磁盘空间

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/your-username/CNN-.git
cd CNN-
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 下载模型
```bash
python scripts/download_models.py
```

## 使用说明

### 启动应用
```bash
python app/main.py
```

### 基本操作
1. 通过"文件"菜单或拖放导入图像
2. 选择分析模式（单图/批量）
3. 点击"开始分析"按钮
4. 查看结果并导出报告

### 注意事项
- 支持的图像格式：JPG、PNG
- 建议图像分辨率：≥800万像素
- 批量处理上限：100张图片
- 单个文件大小限制：20MB

## 许可协议

本项目采用双重许可证模式：

### 开源许可证
对于科研、教育等非商业用途，本项目采用 [GNU Affero General Public License v3.0](docs/legal/LICENSE.txt) 开源协议。该协议要求：

1. 任何修改和分发本软件的行为必须开源
2. 若在网络服务中使用本软件，也需要开放源代码
3. 必须保留原始版权声明
4. 不提供任何担保

### 商业许可证（暂定模板/未实施）
对于商业用途，将需要获取商业许可证。[查看商业许可详情](docs/legal/COMMERCIAL_LICENSE.md)

商业许可将包括：
- 豁免AGPL-3.0开源要求
- 允许闭源使用和修改
- 提供技术支持和定制服务
- 专利授权

**注意**：商业许可系统目前正在开发中，尚未实施。暂不接受商业用途申请。具体条款和定价策略将根据实际需求进行调整。

联系方式（待更新）：
- 邮箱：[commercial@example.com](mailto:commercial@example.com)
- 电话：+86-XXX-XXXX-XXXX

## 字体许可声明

本项目使用了小米MiSans字体。根据《MiSans 字体知识产权许可协议》，特此说明：

1. 本软件使用了MiSans字体
2. MiSans字体的知识产权归小米科技有限责任公司所有
3. 本软件仅将MiSans字体用于界面显示，不进行单独分发或商业用途
4. 字体许可详情请访问：[小米字体授权协议](https://hyperos.mi.com/font)

小米公司授予本项目一份不可转让的、非独占的、免版税的、可撤销的、全球性的版权许可，允许在符合协议条件的情况下使用MiSans字体。

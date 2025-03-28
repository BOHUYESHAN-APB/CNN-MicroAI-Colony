菌落计数系统 - 详细软件文档 (Apache 2.0)
1. 文档概述
许可证声明
本软件及其文档采用 Apache License 2.0 开源协议发布，允许用户在遵守协议条款的前提下自由使用、修改和分发软件。

2. 软件安装与配置
2.1 系统要求
操作系统: Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+

硬件要求:

最低配置: 4GB RAM, 2GB 显存, 10GB 存储空间

推荐配置: 16GB RAM, NVIDIA GPU (支持CUDA 11.0+), 20GB 存储空间

依赖环境: Python 3.8+, PySide6, OpenCV, PyTorch 1.10+

2.2 安装步骤
Windows安装:

下载安装包 ColonyCounter_Setup.exe

双击运行安装向导

选择安装路径 (默认: C:\Program Files\ColonyCounter)

选择是否创建桌面快捷方式

完成安装

Linux/macOS安装:

bash
复制
tar -xzf ColonyCounter_Linux.tar.gz
cd ColonyCounter
./install.sh
3. 用户界面详解
3.1 主界面布局
复制
+-----------------------------------------------------------+
| 菜单栏                                                    |
+-------------------+---------------------------+-----------+
| 项目面板          |                           | 参数面板  |
| (可折叠)          |                           | (可折叠)  |
|                   |                           |           |
| - 图像列表        |                           | - 模型    |
| - 项目树          |                           | - 预处理  |
|                   |                           | - 后处理  |
|                   |                           |           |
|                   |                           |           |
+-------------------+     主视图区域            +-----------+
|                   |                           |           |
|                   |                           |           |
|                   |                           |           |
| 工具面板          | 图像显示与分析结果        | 结果面板  |
| (可折叠)          |                           | (可折叠)  |
| - 视图工具        |                           | - 统计    |
| - 标注工具        |                           | - 图表    |
|                   |                           |           |
+-------------------+---------------------------+-----------+
| 状态栏                                                    |
+-----------------------------------------------------------+
3.2 菜单栏功能
文件菜单
新建项目 (Ctrl+N): 创建空白项目

弹出对话框设置项目名称和保存路径

打开项目 (Ctrl+O): 加载已有项目文件 (.ccproj)

文件选择对话框过滤.ccproj文件

保存项目 (Ctrl+S): 保存当前项目

首次保存会弹出路径选择对话框

另存为...: 将项目另存为新文件

导入图像 (Ctrl+I): 添加图像到当前项目

支持多选: JPG/PNG/BMP/TIFF

选项: 是否复制到项目目录

导出结果:

导出为CSV (Ctrl+E): 将计数结果导出为表格

导出标记图像 (Ctrl+Shift+E): 保存带标记的原图

导出报告 (Ctrl+R): 生成PDF格式完整报告

退出 (Alt+F4): 关闭应用程序

编辑菜单
撤销 (Ctrl+Z): 撤销上一步操作

重做 (Ctrl+Y): 重做撤销的操作

参数预设:

保存当前预设: 将当前参数组合保存为预设

管理预设: 查看/删除已有预设

首选项 (Ctrl+,): 打开设置对话框

常规选项卡:

语言选择 (需重启生效)

主题选择 (即时生效)

默认项目路径

显示选项卡:

标记颜色设置

字体大小调整

高DPI缩放设置

性能选项卡:

GPU加速开关

线程数设置

缓存大小设置

视图菜单
面板控制:

显示/隐藏项目面板 (Ctrl+1)

显示/隐藏参数面板 (Ctrl+2)

显示/隐藏结果面板 (Ctrl+3)

显示/隐藏工具面板 (Ctrl+4)

布局管理:

重置布局: 恢复默认布局

保存当前布局: 保存自定义布局

加载布局: 选择已有布局

缩放控制:

放大 (Ctrl+=)

缩小 (Ctrl+-)

实际大小 (Ctrl+0)

适应窗口 (Ctrl+9)

处理菜单
运行分析 (F5): 对当前图像执行分析

状态栏显示进度条

完成后播放提示音

批量处理 (Ctrl+F5): 处理项目中的所有图像

弹出对话框选择处理顺序和并发数

停止处理 (Esc): 中断正在运行的分析

重新处理 (F6): 使用相同参数重新分析

手动修正:

添加菌落: 在图像上点击添加遗漏菌落

删除菌落: 点击已有标记删除误检

调整大小: 拖动标记边缘调整菌落大小

帮助菜单
用户手册 (F1): 打开本PDF文档

示例项目: 加载内置示例项目

检查更新: 联网检查新版本

关于: 显示版本和版权信息

包含Apache 2.0许可证链接

3.3 工具栏按钮
复制
[新建] [打开] [保存] | [导入] [导出] | [撤销] [重做] | [放大] [缩小] [适应窗口] | [分析] [批量] [停止] | [帮助]
鼠标悬停显示工具提示

右键点击可自定义工具栏

3.4 项目面板
图像列表
缩略图视图 (可调整大小)

列表视图 (显示文件名、尺寸、状态)

右键菜单:

设为当前: 在主视图显示

分析选中项: 只处理选中的图像

从项目中移除

属性: 查看EXIF信息

项目树
按文件夹结构组织

支持拖拽排序

右键菜单:

新建文件夹

重命名

删除

3.5 参数面板
模型选项卡
选择模型 下拉框:

Faster R-CNN ResNet50 (默认)

YOLOv11

(高级) 自定义模型...

GPU加速 复选框

置信度阈值 滑块 (0.1-0.9, 默认0.5)

高级设置 按钮:

模型输入尺寸

非极大抑制阈值

推理批大小

预处理选项卡
自动预处理 复选框 (默认开启)

手动设置:

CLAHE:

剪裁限制 (默认2.0)

网格大小 (默认8x8)

高斯模糊:

核大小 (默认3x3)

边缘检测:

低阈值 (默认50)

高阈值 (默认150)

重置为默认 按钮

后处理选项卡
菌落大小过滤:

最小直径 (px)

最大直径 (px)

重叠处理:

合并阈值 (默认0.3)

形状过滤:

最小圆度 (0-1)

保存为默认 按钮

3.6 结果面板
统计选项卡
表格显示关键指标:

菌落总数

平均直径 (px/mm)

覆盖面积 (%)

处理时间 (ms)

复制数据 按钮

图表选项卡
分布图表选择:

大小分布直方图

置信度分布折线图

空间分布热图

图表工具栏:

保存图像

调整比例

导出数据

4. 核心功能操作流程
4.1 标准分析流程
文件 → 新建项目

文件 → 导入图像 选择培养皿照片

在参数面板调整设置 (或使用默认)

处理 → 运行分析 或点击工具栏分析按钮

查看结果面板中的统计数据

文件 → 导出结果 保存分析报告

4.2 批量处理流程
导入多张图像 (支持拖拽)

处理 → 批量处理

在对话框设置:

处理顺序 (按名称/随机)

并发数量 (1-4)

完成后操作 (关机/休眠/无)

查看批量结果摘要

4.3 手动修正流程
完成自动分析后，在工具面板选择 手动修正工具

使用:

添加工具: 点击图像添加遗漏菌落

删除工具: 点击已有标记删除

调整工具: 拖动标记边缘

修正后统计自动更新

5. 高级功能
5.1 自定义模型
参数面板 → 模型 → 自定义模型...

指定:

模型权重文件 (.pt/.pth)

配置文件 (.yaml)

类别标签文件 (.txt)

测试模型性能

5.2 脚本扩展
支持Python脚本扩展:

python
复制
from colony_counter import AnalysisPipeline

pipeline = AnalysisPipeline()
pipeline.load_config("my_config.json")
results = pipeline.process_folder("input_images/")
results.export_csv("output.csv")
5.3 命令行接口
复制
colony-counter-cli [OPTIONS] IMAGE_PATH

Options:
  --model TEXT      模型选择 (fasterrcnn/yolov11/custom)
  --output TEXT     输出路径
  --batch INTEGER   批大小
  --gpu / --no-gpu  启用GPU
6. 常见问题解答
Q: 如何提高小菌落的检测率?
A: 1) 降低置信度阈值 2) 减小最小直径设置 3) 使用CLAHE增强对比度

Q: 分析速度慢怎么办?
A: 1) 启用GPU加速 2) 减小批大小 3) 降低输入图像分辨率

Q: 如何分离重叠菌落?
A: 1) 启用分水岭算法 2) 调整重叠阈值 3) 使用手动分割工具

7. 技术支持与反馈
问题报告: GitHub Issues

社区支持: Discourse论坛

商业支持: eg:contact@colonycounter.com

Apache 2.0 License Notice
Copyright [yyyy] [name of copyright owner]
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


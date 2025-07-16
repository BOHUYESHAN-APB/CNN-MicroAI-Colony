# CNN-MicroAI-Colony HTML网站 - 部署说明

> 完全自包含的HTML网站，适合HEXO博客平台部署

## 📁 网站结构

```
docs/html/
├── index.html              # 🏠 主页 - 平台概览
├── cnn-demo.html           # 🧠 CNN深度学习系统展示
├── opencv-demo.html        # 👁️ OpenCV检测系统展示
├── tech-comparison.html    # 📊 技术对比分析
├── documentation.html      # 📚 技术文档中心
└── README.md              # 📋 部署说明 (本文件)
```

## ✨ 网站特色

### 🎨 设计特点
- **完全自包含**：所有CSS和JavaScript内嵌在HTML中
- **HEXO友好**：专为HEXO博客平台优化，避免外部依赖
- **响应式设计**：适配桌面、平板、移动设备
- **现代化UI**：专业的暗色主题，与软件界面风格一致
- **相对链接**：所有页面间使用相对路径链接

### 📄 页面内容

#### 🏠 主页 (index.html)
- 平台概述和核心特色
- 技术架构展示
- 应用场景介绍
- 性能指标表格
- 快速体验入口

#### 🧠 CNN展示页 (cnn-demo.html)
- 深度学习模型架构详解
- 性能指标和技术创新
- 应用案例展示
- 训练数据集介绍
- 部署方案说明

#### 👁️ OpenCV展示页 (opencv-demo.html)
- 传统CV算法原理详解
- 检测精度验证结果
- GUI界面系统介绍
- 实际应用案例
- 最佳实践建议

#### 📊 技术对比页 (tech-comparison.html)
- CNN vs OpenCV全面对比
- 应用场景决策矩阵
- 技术融合策略
- 性能基准测试
- 未来发展趋势

#### 📚 文档中心 (documentation.html)
- 完整文档分类导航
- 核心文档详情介绍
- 快速导航和资源链接
- 版本维护信息

## 🚀 部署方法

### 方法一：直接部署到HEXO

1. **复制文件到HEXO博客**
```bash
# 假设您的HEXO博客在 blog/ 目录
cp docs/html/*.html blog/source/microai/
```

2. **配置HEXO**
在HEXO的 `_config.yml` 中添加：
```yaml
skip_render:
  - "microai/*.html"
```

3. **生成和部署**
```bash
cd blog/
hexo generate
hexo deploy
```

4. **访问博客**
最终博客地址为：[https://bohuyeshan.top/CNN-MICROAI-COLONY/index.html](https://bohuyeshan.top/CNN-MICROAI-COLONY/index.html)

### 方法二：作为独立页面部署

1. **上传到任何支持静态HTML的服务器**
2. **访问入口**：`https://your-domain.com/path/to/index.html`
3. **页面间导航**：通过相对链接自动跳转

### 方法三：GitHub Pages部署

1. **创建新仓库** `microai-website`
2. **上传所有HTML文件**
3. **启用GitHub Pages**
4. **访问**：`https://username.github.io/microai-website/`

## ⚠️ 重要说明

### 🔧 HEXO兼容性
- **CSS内嵌**：所有样式都写在`<style>`标签内，避免外部CSS文件
- **JS内嵌**：所有脚本都写在`<script>`标签内，避免外部JS文件
- **相对链接**：使用`./page.html`格式，确保在任何目录下都能正常工作
- **无外部依赖**：不依赖任何CDN或外部资源

### 📊 性能数据修正
所有涉及CNN模型推理速度的地方都已标记为：
- **"量化评估中"**
- **"待测定"**
- **"性能测试进行中"**

确保不假定未经验证的性能数据。

### 🖼️ 图片处理
当前HTML中图片使用占位符路径，部署时需要：
1. 准备实际的系统截图
2. 将图片放在相对路径下（如`./images/`目录）
3. 更新HTML中的图片路径

## 🎯 内容特色

### 📋 技术准确性
- **真实测试数据**：OpenCV系统基于实际测试结果
- **专业术语**：使用标准的微生物学和计算机视觉术语
- **客观对比**：不夸大任何技术方案的能力

### 🔍 深度技术内容
- **算法原理**：详细的代码示例和技术解释
- **性能分析**：基于实际测试的性能对比
- **应用案例**：真实的医院和实验室应用场景
- **未来规划**：清晰的技术发展路线图

### 💡 用户友好
- **分层阅读**：从概览到技术细节的渐进式内容
- **直观导航**：清晰的页面间跳转和内容索引
- **移动适配**：优秀的移动设备浏览体验

## 🔗 页面链接关系

```
index.html (主页)
├── → cnn-demo.html (CNN系统)
├── → opencv-demo.html (OpenCV系统)
├── → tech-comparison.html (技术对比)
└── → documentation.html (文档中心)

所有页面都可以互相跳转，形成完整的网站结构
```

## 🛠️ 自定义指南

### 修改样式
每个HTML文件的`<style>`标签内包含完整的CSS，可以：
- 修改颜色变量（`:root`部分）
- 调整布局参数
- 添加新的样式类

### 添加内容
- 直接编辑HTML文件
- 保持现有的结构和class命名
- 确保响应式设计兼容性

### 更新链接
如果需要修改页面文件名，记得同时更新：
- 所有页面的导航菜单
- 相互引用的链接
- README文档中的说明

## 📞 技术支持

如果在部署过程中遇到问题：
1. 检查HEXO的`skip_render`配置
2. 确认文件路径的正确性
3. 验证HTML文件的完整性
4. 测试在不同浏览器中的兼容性

---

*部署指南版本：v1.1*  
*创建时间：2025年7月15日*  
*适用平台：HEXO博客、GitHub Pages、静态网站托管*  
*兼容性：所有现代浏览器*

## 🎉 部署完成效果

部署成功后，您将获得：
- ✅ 5个完整的技术展示页面
- ✅ 专业的微生物检测系统介绍
- ✅ 详细的技术对比和分析
- ✅ 完善的文档导航系统
- ✅ 适合所有设备的响应式体验

## 🧬 微生物技术补充说明

1. **数据收集状态**：微生物种类识别功能正在开发中，当前处于数据收集阶段
2. **模型兼容性**：ResNet50/YOLOv11模型需要`models-colony-counting`目录下的模型文件
3. **标注规范**：新标注方法文档位于`docs/technical/TECHNICAL_SPECS_CN.md`
**准备部署您的微生物智能分析平台展示网站！** 🚀
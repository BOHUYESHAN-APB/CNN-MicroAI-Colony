"""
生成MicroAI Colony项目logo
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle

# 创建画布
fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
ax.set_aspect('equal')
ax.axis('off')

# 设置背景色
fig.patch.set_facecolor('#f5f5f5')
ax.set_facecolor('#f5f5f5')

# 绘制菌落图形
colony_color = '#4CAF50'  # 绿色主题
for i in range(5):
    x = 1 + i * 1.5
    y = 2
    size = 0.3 + i * 0.1
    circle = Circle((x, y), size, 
                   facecolor=colony_color,
                   edgecolor='white',
                   linewidth=1.5,
                   alpha=0.8)
    ax.add_patch(circle)

# 添加项目名称
ax.text(4.5, 2, 'MicroAI Colony', 
        fontsize=24, fontweight='bold',
        ha='center', va='center',
        color='#333333')

# 添加副标题
ax.text(4.5, 1.5, 'Bacterial Colony Analysis System',
        fontsize=12, 
        ha='center', va='center',
        color='#666666')

# 设置坐标范围
ax.set_xlim(0, 9)
ax.set_ylim(0, 4)

# 保存logo
plt.tight_layout()
plt.savefig('docs/image/logo.png', bbox_inches='tight', dpi=300)
print("Logo已生成并保存到 docs/image/logo.png")

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit,
                              QLabel, QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt
from typing import List
from pathlib import Path
import numpy as np

from core.models import PetriDish, Colony

class ReportView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("检测报告")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 统计信息表格
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["项目", "值"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # 详细信息文本框
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
    def clear(self):
        """清空报告内容"""
        self.stats_table.setRowCount(0)
        self.details_text.clear()
        
    def update_report(self, dishes: List[PetriDish]):
        """更新报告内容"""
        self.clear()
        
        if not dishes:
            return
            
        # 统计基本信息
        total_colonies = sum(len(dish.colonies) for dish in dishes)
        total_primary_zones = sum(
            sum(1 for colony in dish.colonies if colony.primary_inhibition_zone)
            for dish in dishes
        )
        total_secondary_zones = sum(
            sum(1 for colony in dish.colonies if colony.secondary_inhibition_zone)
            for dish in dishes
        )
        total_overlap_zones = sum(
            sum(1 for colony in dish.colonies if colony.overlap_zones)
            for dish in dishes
        )
        
        # 更新统计表格
        stats = [
            ("培养皿数量", len(dishes)),
            ("总菌落数", total_colonies),
            ("主抑菌圈数量", total_primary_zones),
            ("次级抑菌圈数量", total_secondary_zones),
            ("重叠区域数量", total_overlap_zones),
        ]
        
        self.stats_table.setRowCount(len(stats))
        for row, (item, value) in enumerate(stats):
            self.stats_table.setItem(row, 0, QTableWidgetItem(str(item)))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
        
        # 生成详细报告
        details = []
        for i, dish in enumerate(dishes, 1):
            details.append(f"培养皿 {i}:")
            details.append(f"- 直径: {dish.diameter_mm:.1f}mm")
            details.append(f"- 中心坐标: ({dish.center[0]}, {dish.center[1]})")
            details.append(f"- 包含菌落数: {len(dish.colonies)}")
            
            for j, colony in enumerate(dish.colonies, 1):
                details.append(f"\n菌落 {j}:")
                details.append(f"- 中心坐标: ({colony.center[0]}, {colony.center[1]})")
                details.append(f"- 半径: {colony.radius}px")
                
                # 计算比例尺
                mm_per_pixel = dish.diameter_mm / (2 * dish.radius)
                colony_diameter = 2 * colony.radius * mm_per_pixel
                details.append(f"- 滤纸片直径: {colony_diameter:.1f}mm")
                
                # 主抑菌圈分析
                if colony.primary_inhibition_zone:
                    x, y, r = colony.primary_inhibition_zone
                    zone_diameter = 2 * r * mm_per_pixel
                    zone_width = (zone_diameter - 6.0) / 2  # 6.0mm是标准滤纸片直径
                    details.append("- 主抑菌圈:")
                    details.append(f"  * 直径: {zone_diameter:.1f}mm")
                    details.append(f"  * 抑菌环宽度: {zone_width:.1f}mm")
                    
                # 次级抑菌圈分析
                if colony.secondary_inhibition_zone:
                    x, y, r = colony.secondary_inhibition_zone
                    zone_diameter = 2 * r * mm_per_pixel
                    zone_width = (zone_diameter - 6.0) / 2
                    details.append("- 次级抑菌圈(半透明):")
                    details.append(f"  * 直径: {zone_diameter:.1f}mm")
                    details.append(f"  * 抑菌环宽度: {zone_width:.1f}mm")
                    
                # 重叠区域分析
                if colony.overlap_zones:
                    total_area = sum(np.pi * r * r * (mm_per_pixel ** 2)
                                   for _, _, r in colony.overlap_zones)
                    details.append("- 重叠区域:")
                    details.append(f"  * 总面积: {total_area:.1f}mm²")
                    details.append(f"  * 区域数量: {len(colony.overlap_zones)}")
                    
                    # 详细区域信息
                    for k, (x, y, r) in enumerate(colony.overlap_zones, 1):
                        area = np.pi * r * r * (mm_per_pixel ** 2)
                        details.append(f"  * 区域 {k}:")
                        details.append(f"    - 面积: {area:.1f}mm²")
                        details.append(f"    - 直径: {2 * r * mm_per_pixel:.1f}mm")
                        
            details.append("\n" + "-"*50)
            
        self.details_text.setPlainText("\n".join(details))
        
    def save_report(self, file_path: Path):
        """保存报告到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            # 写入统计信息
            f.write("统计信息:\n")
            f.write("="*50 + "\n")
            for row in range(self.stats_table.rowCount()):
                item = self.stats_table.item(row, 0).text()
                value = self.stats_table.item(row, 1).text()
                f.write(f"{item}: {value}\n")
            
            f.write("\n详细信息:\n")
            f.write("="*50 + "\n")
            # 写入详细信息
            f.write(self.details_text.toPlainText())
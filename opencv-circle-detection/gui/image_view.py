from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QMenu
from PySide6.QtCore import Qt, QSize, QPoint, QPointF, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QFont, QContextMenuEvent

class ImageViewer(QWidget):
    annotation_added = Signal(str, QPointF)  # 新增标注信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 图像相关变量
        self.scale_factor = 1.0
        self.original_pixmap = None
        self.annotations = []  # 存储标注信息: [(text, point), ...]
        
        # 标注相关变量
        self.current_annotation = None
        self.annotation_font = QFont("Arial", 12)
        self.annotation_color = QColor(255, 0, 0)  # 红色
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(1, 1)
        
        # 将标签添加到滚动区域
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
    def set_image(self, image: QImage):
        """设置要显示的图像"""
        if image.isNull():
            return
            
        # 保存原始图像
        self.original_pixmap = QPixmap.fromImage(image)
        
        # 调整大小以适应窗口
        self.scale_to_fit()
        
    def scale_to_fit(self):
        """缩放图像以适应窗口"""
        if not self.original_pixmap:
            return
            
        # 获取可用空间
        available_size = self.scroll_area.viewport().size()
        
        # 计算缩放因子
        scale_w = available_size.width() / self.original_pixmap.width()
        scale_h = available_size.height() / self.original_pixmap.height()
        self.scale_factor = min(scale_w, scale_h)
        
        # 应用缩放
        self.update_image()
        
    def update_image(self):
        """更新显示的图像"""
        if not self.original_pixmap:
            return
            
        # 计算新大小
        new_size = QSize(
            int(self.original_pixmap.width() * self.scale_factor),
            int(self.original_pixmap.height() * self.scale_factor)
        )
        
        # 创建缩放后的图像
        scaled_pixmap = self.original_pixmap.scaled(
            new_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # 创建工作副本用于绘制
        working_pixmap = QPixmap(scaled_pixmap)
        painter = QPainter(working_pixmap)
        
        # 设置绘制属性
        painter.setFont(self.annotation_font)
        painter.setPen(QPen(self.annotation_color, 2))
        
        # 绘制所有标注
        for text, point in self.annotations:
            scaled_point = QPointF(
                point.x() * self.scale_factor,
                point.y() * self.scale_factor
            )
            # 画点
            painter.drawEllipse(scaled_point, 3, 3)
            # 画文本
            painter.drawText(
                scaled_point.x() + 5,
                scaled_point.y() + 5,
                text
            )
            
        painter.end()
        
        # 更新标签
        self.image_label.setPixmap(working_pixmap)
        
    def wheelEvent(self, event):
        """鼠标滚轮事件处理"""
        if not self.original_pixmap:
            return
            
        # 计算新的缩放因子
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_factor *= 1.1
        else:
            self.scale_factor /= 1.1
            
        # 限制缩放范围
        self.scale_factor = min(max(0.1, self.scale_factor), 10.0)
        
        # 更新图像
        self.update_image()
        
    def resizeEvent(self, event):
        """窗口大小改变事件处理"""
        super().resizeEvent(event)
        # 调整图像大小以适应新窗口
        self.scale_to_fit()
        
    def add_annotation(self, text: str):
        """添加新标注"""
        self.current_annotation = text
        # 设置鼠标追踪，以便接收鼠标移动事件
        self.image_label.setMouseTracking(True)
        # 改变鼠标形状
        self.setCursor(Qt.CrossCursor)
        
    def mousePressEvent(self, event):
        """鼠标按下事件处理"""
        if event.button() == Qt.LeftButton and self.current_annotation:
            # 获取相对于图像的坐标
            pos = self.image_label.mapFrom(self, event.pos())
            image_pos = QPointF(
                pos.x() / self.scale_factor,
                pos.y() / self.scale_factor
            )
            
            # 添加标注
            self.annotations.append((self.current_annotation, image_pos))
            
            # 发送信号
            self.annotation_added.emit(self.current_annotation, image_pos)
            
            # 重置当前标注状态
            self.current_annotation = None
            self.setCursor(Qt.ArrowCursor)
            self.image_label.setMouseTracking(False)
            
            # 更新显示
            self.update_image()
            
    def contextMenuEvent(self, event: QContextMenuEvent):
        """右键菜单事件处理"""
        menu = QMenu(self)
        
        # 添加清除所有标注的动作
        clear_action = menu.addAction("清除所有标注")
        clear_action.triggered.connect(self.clear_annotations)
        
        # 显示菜单
        menu.exec(event.globalPos())
        
    def clear_annotations(self):
        """清除所有标注"""
        self.annotations.clear()
        self.update_image()
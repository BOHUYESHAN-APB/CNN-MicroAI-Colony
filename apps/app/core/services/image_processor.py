import os
import cv2
import numpy as np
from typing import Optional, Dict, List
import logging
from ..models import ImageData
from ..events import ImageLoadedEvent, ProcessingCompletedEvent

logger = logging.getLogger(__name__)

class ImageProcessor:
    """图像处理服务核心类"""
    
    def __init__(self):
        self._pipeline = []
        self._current_image: Optional[ImageData] = None
        self._processing_stack: List[ImageData] = []
        
    def load_image(self, path: str) -> bool:
        """加载图像并初始化处理流水线"""
        try:
            abs_path = os.path.abspath(path)
            if os.name == 'nt':
                abs_path = rf'\\?\{abs_path}'
                
            image = cv2.imdecode(np.fromfile(abs_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"无法读取图像文件: {abs_path}")
                return False
                
            self._current_image = ImageData(
                original=image,
                path=abs_path,
                metadata=self._extract_metadata(abs_path)
            )
            self._processing_stack.clear()
            logger.info(f"成功加载图像: {abs_path}")
            ImageLoadedEvent(self._current_image).dispatch()
            return True
            
        except Exception as e:
            logger.error(f"图像加载异常: {str(e)}")
            return False

    def _extract_metadata(self, path: str) -> Dict:
        """提取图像元数据"""
        return {
            'path': path,
            'size': os.path.getsize(path),
            'created': os.path.getctime(path),
            'modified': os.path.getmtime(path)
        }

    def add_processing_step(self, step: callable):
        """添加处理步骤到流水线"""
        self._pipeline.append(step)
        logger.debug(f"添加处理步骤: {step.__name__}")

    async def process_image(self):
        """异步执行图像处理流水线"""
        if not self._current_image:
            logger.warning("无可用图像进行处理")
            return
            
        try:
            current = self._current_image
            for step in self._pipeline:
                current = await self._apply_processing_step(current, step)
                self._processing_stack.append(current)
                
            ProcessingCompletedEvent(current).dispatch()
            logger.info("图像处理流程完成")
        except Exception as e:
            logger.error(f"处理过程中出错: {str(e)}")
            raise

    async def _apply_processing_step(self, image_data: ImageData, step: callable) -> ImageData:
        """应用单个处理步骤"""
        logger.debug(f"执行处理步骤: {step.__name__}")
        try:
            processed_image = await step(image_data)
            return ImageData(
                original=processed_image,
                path=image_data.path,
                metadata=image_data.metadata,
                parent=image_data
            )
        except Exception as e:
            logger.error(f"处理步骤{step.__name__}执行失败: {str(e)}")
            raise

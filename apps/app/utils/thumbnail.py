"""
Thumbnail Generator
缩略图生成器
"""
import os
import logging
from typing import Optional
from PIL import Image
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    """Thumbnail generator with caching"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".colony_analyzer", "thumbs")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_thumbnail(self, image_path: str, size: int = 200) -> Optional[QPixmap]:
        """Get thumbnail for image, create if not exists"""
        try:
            # Get cache path
            cache_name = f"{os.path.basename(image_path)}_{size}.jpg"
            cache_path = os.path.join(self.cache_dir, cache_name)
            
            # Return cached thumbnail if exists
            if os.path.exists(cache_path):
                thumb = QImage(cache_path)
                if not thumb.isNull():
                    return QPixmap.fromImage(thumb)
            
            # Create thumbnail
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                # Calculate new size keeping aspect ratio
                ratio = min(size / img.width, size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                # Resize image
                thumb = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Save to cache
                thumb.save(cache_path, "JPEG", quality=85)
                
                # Convert to QPixmap
                qimg = QImage(cache_path)
                return QPixmap.fromImage(qimg)
                
        except Exception as e:
            logger.error(f"Failed to create thumbnail for {image_path}: {e}")
            return None
            
    def clear_cache(self):
        """Clear thumbnail cache"""
        try:
            for file in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, file))
            logger.info("Thumbnail cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear thumbnail cache: {e}")

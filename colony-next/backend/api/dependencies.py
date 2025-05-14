from functools import lru_cache
from pathlib import Path
from typing import Generator

from core.image_processor import ImageProcessor
from core.model_manager import ModelManager
from core.camera_manager import CameraManager
from core.websocket_manager import ws_manager

@lru_cache()
def get_settings():
    """获取应用设置"""
    return {
        "UPLOAD_DIR": Path("uploads"),
        "MODEL_DIR": Path("models"),
        "MAX_UPLOAD_SIZE": 10 * 1024 * 1024,  # 10MB
        "SUPPORTED_FORMATS": [".jpg", ".jpeg", ".png", ".bmp"],
        "DEFAULT_RESOLUTION": "1920x1080",
        "DEFAULT_FPS": 30,
    }

def get_image_processor() -> Generator[ImageProcessor, None, None]:
    """获取图像处理器实例"""
    processor = ImageProcessor()
    try:
        yield processor
    finally:
        # 清理资源
        pass

def get_model_manager() -> Generator[ModelManager, None, None]:
    """获取模型管理器实例"""
    manager = ModelManager()
    try:
        yield manager
    finally:
        # 清理资源
        manager.cleanup()

def get_camera_manager() -> Generator[CameraManager, None, None]:
    """获取相机管理器实例"""
    manager = CameraManager()
    try:
        yield manager
    finally:
        # 释放相机
        manager.release()

def get_websocket_manager():
    """获取WebSocket管理器实例"""
    return ws_manager

def verify_upload_file(file_path: Path, settings: dict) -> bool:
    """验证上传文件"""
    # 检查文件大小
    if file_path.stat().st_size > settings["MAX_UPLOAD_SIZE"]:
        return False
        
    # 检查文件格式
    if file_path.suffix.lower() not in settings["SUPPORTED_FORMATS"]:
        return False
        
    return True

def create_upload_dir(settings: dict):
    """创建上传目录"""
    upload_dir = settings["UPLOAD_DIR"]
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir

def cleanup_upload_dir(settings: dict):
    """清理上传目录中的临时文件"""
    upload_dir = settings["UPLOAD_DIR"]
    for file in upload_dir.glob("*"):
        if file.is_file():
            try:
                file.unlink()
            except Exception:
                pass

def init_resources(settings: dict):
    """初始化资源"""
    # 创建必要的目录
    create_upload_dir(settings)
    
    # 加载模型
    model_manager = ModelManager()
    model_dir = settings["MODEL_DIR"]
    model_manager.load_models_from_dir(model_dir)
    
    # 初始化相机
    camera_manager = CameraManager()
    width, height = map(int, settings["DEFAULT_RESOLUTION"].split("x"))
    camera_manager.frame_width = width
    camera_manager.frame_height = height
    camera_manager.fps = settings["DEFAULT_FPS"]
    
    return {
        "model_manager": model_manager,
        "camera_manager": camera_manager
    }

def cleanup_resources(resources: dict):
    """清理资源"""
    # 清理模型管理器
    if "model_manager" in resources:
        resources["model_manager"].cleanup()
        
    # 释放相机
    if "camera_manager" in resources:
        resources["camera_manager"].release()
        
    # 清理WebSocket连接
    ws_manager.cleanup()
    
    # 清理上传目录
    settings = get_settings()
    cleanup_upload_dir(settings)

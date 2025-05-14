import cv2
import numpy as np
from typing import Dict, Tuple, Optional

class CameraManager:
    """相机管理类"""
    
    def __init__(self):
        self.camera = None
        self.camera_index = 0
        self.is_running = False
        self.frame_width = 1920
        self.frame_height = 1080
        self.fps = 30
        self._accelerometer_data = {"x": 0, "y": 0, "z": 0}
        
    def initialize(self, camera_index: int = 0) -> bool:
        """初始化相机"""
        try:
            self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                return False
                
            # 设置分辨率
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.camera_index = camera_index
            self.is_running = True
            return True
            
        except Exception as e:
            print(f"相机初始化失败: {str(e)}")
            return False
            
    def release(self):
        """释放相机资源"""
        if self.camera is not None:
            self.is_running = False
            self.camera.release()
            self.camera = None
            
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """获取一帧图像"""
        if not self.is_running or self.camera is None:
            return False, None
            
        ret, frame = self.camera.read()
        if not ret:
            return False, None
            
        return True, frame
        
    def update_accelerometer(self, x: float, y: float, z: float):
        """更新加速度计数据"""
        self._accelerometer_data = {
            "x": x,
            "y": y,
            "z": z
        }
        
    def get_tilt_angles(self) -> Tuple[float, float]:
        """
        获取倾斜角度
        返回: (x轴倾斜角度, y轴倾斜角度)
        """
        x = self._accelerometer_data["x"]
        y = self._accelerometer_data["y"]
        z = self._accelerometer_data["z"]
        
        # 计算倾斜角度
        # 这里使用简单的三角函数计算
        # 实际使用时可能需要更复杂的算法
        try:
            x_angle = np.arctan2(x, np.sqrt(y*y + z*z)) * 180.0 / np.pi
            y_angle = np.arctan2(y, np.sqrt(x*x + z*z)) * 180.0 / np.pi
            return x_angle, y_angle
        except:
            return 0.0, 0.0
            
    def get_camera_info(self) -> Dict:
        """获取相机信息"""
        return {
            "status": "running" if self.is_running else "stopped",
            "resolution": f"{self.frame_width}x{self.frame_height}",
            "fps": self.fps,
            "camera_index": self.camera_index,
            "tilt": {
                "x": self.get_tilt_angles()[0],
                "y": self.get_tilt_angles()[1]
            }
        }
        
    def set_resolution(self, width: int, height: int) -> bool:
        """设置相机分辨率"""
        if not self.is_running or self.camera is None:
            return False
            
        try:
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # 验证设置是否生效
            actual_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            if abs(actual_width - width) > 1 or abs(actual_height - height) > 1:
                return False
                
            self.frame_width = width
            self.frame_height = height
            return True
            
        except Exception as e:
            print(f"设置分辨率失败: {str(e)}")
            return False
            
    def set_fps(self, fps: int) -> bool:
        """设置相机帧率"""
        if not self.is_running or self.camera is None:
            return False
            
        try:
            self.camera.set(cv2.CAP_PROP_FPS, fps)
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            if abs(actual_fps - fps) > 1:
                return False
                
            self.fps = fps
            return True
            
        except Exception as e:
            print(f"设置帧率失败: {str(e)}")
            return False

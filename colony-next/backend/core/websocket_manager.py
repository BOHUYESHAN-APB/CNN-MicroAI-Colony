import asyncio
from typing import Dict, Set, Callable
import json
from fastapi import WebSocket
import base64
import cv2
import numpy as np
from pathlib import Path

class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "camera": set(),
            "analysis": set()
        }
        self.running_tasks: Set[asyncio.Task] = set()
        
    async def connect(self, websocket: WebSocket, channel: str):
        """建立WebSocket连接"""
        if channel not in self.active_connections:
            raise ValueError(f"Invalid channel: {channel}")
            
        await websocket.accept()
        self.active_connections[channel].add(websocket)
        
    def disconnect(self, websocket: WebSocket, channel: str):
        """断开WebSocket连接"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            
    async def broadcast(self, channel: str, message: Dict):
        """广播消息到指定频道"""
        if channel not in self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
                
        # 清理断开的连接
        for connection in disconnected:
            self.active_connections[channel].discard(connection)
            
    async def start_camera_stream(self, camera, fps: int = 30):
        """启动相机流"""
        interval = 1.0 / fps
        
        while self.active_connections["camera"]:
            try:
                # 获取相机帧
                ret, frame = camera.get_frame()
                if not ret:
                    continue
                    
                # 获取倾斜角度
                x_tilt, y_tilt = camera.get_tilt_angles()
                
                # 编码图像
                _, buffer = cv2.imencode('.jpg', frame)
                base64_image = base64.b64encode(buffer).decode('utf-8')
                
                # 构建消息
                message = {
                    "type": "frame",
                    "data": base64_image,
                    "timestamp": asyncio.get_event_loop().time(),
                    "tilt": {
                        "x": x_tilt,
                        "y": y_tilt
                    }
                }
                
                # 广播帧
                await self.broadcast("camera", message)
                
                # 控制帧率
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"相机流错误: {str(e)}")
                await asyncio.sleep(1)
                
    def start_camera_task(self, camera):
        """创建并启动相机流任务"""
        task = asyncio.create_task(self.start_camera_stream(camera))
        self.running_tasks.add(task)
        task.add_done_callback(self.running_tasks.discard)
        
    async def send_analysis_result(self, result: Dict):
        """发送分析结果"""
        message = {
            "type": "analysis_result",
            "timestamp": asyncio.get_event_loop().time(),
            "data": result
        }
        await self.broadcast("analysis", message)
        
    def cleanup(self):
        """清理资源"""
        # 取消所有运行中的任务
        for task in self.running_tasks:
            task.cancel()
        
        # 清空连接
        for channel in self.active_connections:
            self.active_connections[channel].clear()

# 单例模式
ws_manager = WebSocketManager()

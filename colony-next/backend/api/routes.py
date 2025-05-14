from fastapi import APIRouter, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pathlib import Path
import asyncio

from core.image_processor import ImageProcessor
from core.model_manager import ModelManager
from core.camera_manager import CameraManager
from core.websocket_manager import ws_manager

router = APIRouter()
image_processor = ImageProcessor()
model_manager = ModelManager()
camera_manager = CameraManager()

@router.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "Colony Analysis API is running"}

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """分析单张图片"""
    try:
        # 保存上传的图片
        file_path = Path("uploads") / file.filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # 分析图片
        results = image_processor.analyze_image(file_path)
        
        # 发送结果到WebSocket客户端
        await ws_manager.send_analysis_result(results)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "results": results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calibrate")
async def calibrate_camera(file: UploadFile = File(...)):
    """相机校准"""
    try:
        # 保存校准图片
        file_path = Path("uploads") / file.filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # 执行校准
        scale = image_processor.calculate_scale(file_path)
        
        return JSONResponse(content={
            "status": "success",
            "scale": scale,
            "message": "Camera calibration completed"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings():
    """获取系统设置"""
    camera_info = camera_manager.get_camera_info()
    model_info = model_manager.get_model_info()
    
    return {
        "camera": camera_info,
        "model": model_info,
        "analysis": {
            "confidence_threshold": image_processor.confidence_threshold,
            "min_colony_size": image_processor.min_colony_size,
            "max_colony_size": image_processor.max_colony_size
        }
    }

@router.post("/settings")
async def update_settings(settings: dict):
    """更新系统设置"""
    try:
        if "camera" in settings:
            camera_settings = settings["camera"]
            if "resolution" in camera_settings:
                width, height = map(int, camera_settings["resolution"].split("x"))
                camera_manager.set_resolution(width, height)
            if "fps" in camera_settings:
                camera_manager.set_fps(camera_settings["fps"])
                
        if "analysis" in settings:
            analysis_settings = settings["analysis"]
            if "confidence_threshold" in analysis_settings:
                image_processor.confidence_threshold = float(analysis_settings["confidence_threshold"])
            if "min_colony_size" in analysis_settings:
                image_processor.min_colony_size = int(analysis_settings["min_colony_size"])
                
        return {"status": "success", "message": "Settings updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/camera")
async def websocket_camera_endpoint(websocket: WebSocket):
    """相机预览WebSocket端点"""
    await ws_manager.connect(websocket, "camera")
    try:
        # 启动相机流
        camera_manager.initialize()
        ws_manager.start_camera_task(camera_manager)
        
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            if data == "close":
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        camera_manager.release()
        ws_manager.disconnect(websocket, "camera")

@router.websocket("/ws/analysis")
async def websocket_analysis_endpoint(websocket: WebSocket):
    """分析结果WebSocket端点"""
    await ws_manager.connect(websocket, "analysis")
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "analysis")

@router.post("/batch")
async def batch_analyze(files: list[UploadFile] = File(...)):
    """批量分析图片"""
    try:
        results = []
        for file in files:
            # 保存文件
            file_path = Path("uploads") / file.filename
            file_path.parent.mkdir(exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
                
            # 分析图片
            result = image_processor.analyze_image(file_path)
            results.append({
                "filename": file.filename,
                "results": result
            })
            
        return JSONResponse(content={
            "status": "success",
            "results": results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """获取可用模型列表"""
    return model_manager.get_model_info()

@router.post("/models/{model_name}")
async def set_model(model_name: str):
    """设置当前使用的模型"""
    if model_manager.set_current_model(model_name):
        return {"status": "success", "message": f"Switched to model: {model_name}"}
    else:
        raise HTTPException(status_code=404, detail="Model not found")

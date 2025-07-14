import sys
from pathlib import Path

# Add project root and models-colony-counting to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "models-colony-counting" / "in-use" / "faster_rcnn_resnet50" / "src" / "models"))
import sys
from pathlib import Path

# Add project root and apps/app/core/models to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "apps" / "app" / "core" / "models"))

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import cv2
import numpy as np
import os
import torch

app = FastAPI(title="Colony Analysis Backend")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class ColonyAnalyzer:
    def __init__(self):
        # 加载ColonyDetector模型
        from colony_detector import ColonyDetector
        self.detector = ColonyDetector()  # Important: set 
        # Load the trained weights. Use map_location for CPU if you don't have a GPU.
        self.detector.load_state_dict(torch.load("D:\\train\\checkpoint_epoch_31.pth", map_location=torch.device('cpu')))
        self.detector.eval() # Set the model to evaluation mode
        self.initialized = True # No initialize() method anymore

    def analyze_image(self, image_path: Path):
        """分析图像中的菌落"""
        # 临时修改：忽略图像内容，返回固定结果
        return {
            "count": 10,
            "positions": [],
            "sizes": [],
            "confidence": []
        }

analyzer = ColonyAnalyzer()

@app.get("/")
async def root():
    return {"message": "Colony Analysis Backend is running"}

@app.post("/analyze")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """分析上传的图片"""
    try:
        # 保存上传的文件
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 分析图片
        results = analyzer.analyze_image(file_path)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "results": results
        })
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.post("/calibrate")
async def calibrate_camera(file: UploadFile = File(...)):
    """相机校准"""
    try:
        # 保存校准图片
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # TODO: 实现相机校准逻辑
        
        return JSONResponse(content={
            "status": "success",
            "message": "Camera calibration completed"
        })
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.get("/settings")
async def get_settings():
    """获取系统设置"""
    return {
        "camera": {
            "resolution": "1920x1080",
            "fps": 30
        },
        "analysis": {
            "confidence_threshold": 0.5,
            "min_colony_size": 10
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Flask应用配置
import os

# 基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = 'dev-key'  # 生产环境需要替换

# 模型路径配置
MODEL_PATHS = {
    'lightweight': 'D:\\-Users-\\Documents\\GitHub\\CNN-MicroAI-Colony\\faster_rcnn_resnet50\\checkpoints\\checkpoint_epoch_31.pth',
    'accurate': 'D:\\train\\faster_rcnn_colony_epoch8.pth', 
    'balanced': 'D:\\train\\faster_rcnn_colony_epoch12.pth'
}

# 文件上传配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

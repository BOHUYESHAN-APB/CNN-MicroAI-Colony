import os
import logging
from datetime import datetime

class Logger:
    def __init__(self, config, name="yolov5"):
        self.log_dir = config['log_dir']
        self.checkpoint_dir = config['checkpoint_dir']
        self.model_output_dir = config['model_output']
        
        # 创建目录
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.model_output_dir, exist_ok=True)
        
        # 设置日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"{name}_{timestamp}.log")
        
        # 配置日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, message):
        self.logger.info(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
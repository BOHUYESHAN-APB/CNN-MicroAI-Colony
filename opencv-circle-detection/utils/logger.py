import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger():
    """初始化日志系统"""
    if logging.getLogger().handlers:
        return  # 已经初始化过，直接返回

    # 创建日志目录
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # 配置日志格式
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    setup_logger()  # 确保日志系统已初始化
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger

# 初始化默认日志记录器
default_logger = get_logger("opencv-circle-detection")
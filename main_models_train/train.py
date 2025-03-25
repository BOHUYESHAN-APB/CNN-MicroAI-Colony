import os
import sys
from mmdet.apis import train_detector
from mmdet.datasets import build_dataset
from mmdet.models import build_detector
from mmcv import Config

def main():
    # 加载配置文件
    config_file = 'configs/faster_rcnn_colony.py'
    cfg = Config.fromfile(config_file)
    
    # 确保输出目录存在
    os.makedirs(cfg.work_dir, exist_ok=True)
    
    # 构建模型
    model = build_detector(cfg.model)
    
    # 构建数据集
    datasets = [build_dataset(cfg.data.train)]
    
    # 开始训练
    train_detector(
        model,
        datasets,
        cfg,
        distributed=False,
        validate=True,
        timestamp=None,
        meta=None
    )

if __name__ == '__main__':
    main()

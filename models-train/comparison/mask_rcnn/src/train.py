import argparse
import os
import sys
import torch
from mmcv import Config
from mmdet.apis import train_detector
from mmdet.datasets import build_dataset
from mmdet.models import build_detector
from mmdet.utils import get_root_logger, collect_env

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Train Mask R-CNN for colony detection')
    parser.add_argument('--config', default='../configs/mask_rcnn_coco.py',
                        help='训练配置文件路径')
    parser.add_argument('--work-dir',
                        help='工作目录，用于保存日志和模型')
    parser.add_argument('--resume-from', help='从指定checkpoint恢复训练')
    parser.add_argument('--no-validate', action='store_true',
                        help='训练时不验证')
    parser.add_argument('--gpus', type=int, default=1,
                        help='使用的GPU数量')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子')
    parser.add_argument('--deterministic', action='store_true',
                        help='确定性训练')
    parser.add_argument('--local_rank', type=int, default=0)
    
    return parser.parse_args()


def main():
    """主训练函数"""
    args = parse_args()
    
    cfg = Config.fromfile(args.config)

    # 设置工作目录
    if args.work_dir is not None:
        cfg.work_dir = args.work_dir
    elif cfg.get('work_dir', None) is None:
        cfg.work_dir = os.path.join('./work_dirs',
                                  os.path.splitext(os.path.basename(args.config))[0])
    os.makedirs(cfg.work_dir, exist_ok=True)

    # 创建日志记录器
    timestamp = torch.utils.tensorboard.SummaryWriter().get_logdir().split('/')[-1]
    log_file = os.path.join(cfg.work_dir, f'{timestamp}.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # 记录环境信息
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    dash_line = '-' * 60 + '\n'
    logger.info('Environment info:\n' + dash_line + env_info + '\n' +
                dash_line)

    # 记录配置信息
    logger.info(f'Config:\n{cfg.pretty_text}')

    # 设置随机种子
    if args.seed is not None:
        logger.info(f'Set random seed to {args.seed}')
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)

    # 构建数据集
    datasets = [build_dataset(cfg.data.train)]
    
    # 构建模型
    model = build_detector(
        cfg.model,
        train_cfg=cfg.get('train_cfg'),
        test_cfg=cfg.get('test_cfg'))
    
    # 添加类别信息
    model.CLASSES = datasets[0].CLASSES
    
    # 开始训练
    train_detector(
        model,
        datasets,
        cfg,
        distributed=False,
        validate=not args.no_validate,
        timestamp=timestamp,
        meta=dict())
    
    print("训练完成！")


if __name__ == '__main__':
    main()
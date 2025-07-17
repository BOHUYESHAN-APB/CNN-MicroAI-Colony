"""
Colony detection model training script
菌落检测模型训练脚本
"""
import os
import sys
import copy
import argparse
import logging
from pathlib import Path
import torch

try:
    import mmdet
    from mmdet.apis import train_detector
    from mmdet.models import build_detector
    from mmdet.datasets import build_dataset
    from mmdet.utils import collect_env, get_root_logger
    from mmcv import Config
    from mmcv.runner import load_checkpoint, wrap_fp16_model
    from mmcv.utils import get_git_hash
except ImportError:
    print("请先安装必要的依赖:")
    print("pip install -r main_models_train/requirements.txt")
    sys.exit(1)

def parse_args():
    """
    Parse command line arguments
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='Train colony detector')
    parser.add_argument('config', help='train config file path')
    parser.add_argument('--work-dir', help='the dir to save logs and models')
    parser.add_argument('--resume-from', help='the checkpoint file to resume from')
    parser.add_argument('--no-validate', action='store_true', help='whether not to evaluate the checkpoint during training')
    parser.add_argument('--seed', type=int, default=None, help='random seed')
    parser.add_argument('--gpu-ids', type=int, nargs='+', help='ids of gpus to use')
    args = parser.parse_args()
    return args

def main():
    """Training main function"""
    args = parse_args()

    # Load config
    # 加载配置
    cfg = Config.fromfile(args.config)

    # Set working directory
    # 设置工作目录
    if args.work_dir is not None:
        cfg.work_dir = args.work_dir
    elif cfg.get('work_dir', None) is None:
        cfg.work_dir = os.path.join('./work_dirs',
                                  os.path.splitext(os.path.basename(args.config))[0])
    os.makedirs(cfg.work_dir, exist_ok=True)

    # Create logger
    # 创建日志记录器
    timestamp = torch.utils.tensorboard.SummaryWriter().get_logdir().split('/')[-1]
    log_file = os.path.join(cfg.work_dir, f'{timestamp}.log')
    logger = get_root_logger(log_file=log_file, log_level=cfg.log_level)

    # Log environment info
    # 记录环境信息
    env_info_dict = collect_env()
    env_info = '\n'.join([f'{k}: {v}' for k, v in env_info_dict.items()])
    dash_line = '-' * 60 + '\n'
    logger.info('Environment info:\n' + dash_line + env_info + '\n' +
                dash_line)

    # Log config
    # 记录配置信息
    logger.info(f'Config:\n{cfg.pretty_text}')

    # Set random seeds
    # 设置随机种子
    if args.seed is not None:
        logger.info(f'Set random seed to {args.seed}')
        torch.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)

    # Build datasets
    # 构建数据集
    datasets = [build_dataset(cfg.data.train)]
    
    if len(cfg.workflow) == 2:
        val_dataset = copy.deepcopy(cfg.data.val)
        datasets.append(build_dataset(val_dataset))

    # Build model
    # 构建模型
    model = build_detector(cfg.model)
    model.init_weights()

    # FP16 training
    # FP16训练
    fp16_cfg = cfg.get('fp16', None)
    if fp16_cfg is not None:
        wrap_fp16_model(model)

    # Resume from checkpoint
    # 从检查点恢复
    if args.resume_from:
        logger.info(f'Resume from checkpoint {args.resume_from}')
        load_checkpoint(model, args.resume_from, map_location='cpu')

    # Train model
    # 训练模型
    train_detector(
        model,
        datasets[0],
        cfg,
        distributed=False,
        validate=(not args.no_validate),
        timestamp=timestamp,
        meta=dict(
            mmdet_version=mmdet.__version__ + get_git_hash()[:7],
            config=cfg.pretty_text
        ))

if __name__ == '__main__':
    main()
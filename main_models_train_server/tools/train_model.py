"""
Training launcher script for server deployment
服务器部署训练启动脚本
"""
import os
import sys
import shutil
import argparse
from pathlib import Path
from dataset_preprocessor import DatasetPreprocessor
from performance_estimator import PerformanceEstimator

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Train colony detection model')
    parser.add_argument('--source-dirs', nargs='+', required=True,
                       help='Source dataset directories')
    parser.add_argument('--img-size', nargs=2, type=int, default=[1280, 1280],
                       help='Target image size (width height)')
    parser.add_argument('--work-dir', default='work_dirs',
                       help='Directory to save checkpoints and logs')
    parser.add_argument('--batch-size', type=int, default=4,
                       help='Training batch size')
    parser.add_argument('--epochs', type=int, default=12,
                       help='Number of training epochs')
    parser.add_argument('--no-validate', action='store_true',
                       help='Whether not to evaluate during training')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed')
    args = parser.parse_args()
    return args

def copy_datasets(source_dirs: list, target_dir: Path):
    """
    Copy datasets to train directory
    复制数据集到训练目录
    """
    print("\nStep 1: Copying datasets")
    print("步骤1：复制数据集")
    print("-" * 50)
    
    for src_dir in source_dirs:
        src_path = Path(src_dir)
        if not src_path.exists():
            print(f"Warning: Source directory not found: {src_dir}")
            continue
            
        # Create target directory with same name
        # 创建同名目标目录
        dst_path = target_dir / src_path.name
        if dst_path.exists():
            print(f"Warning: Target directory already exists: {dst_path}")
            continue
            
        try:
            shutil.copytree(src_path, dst_path)
            print(f"Copied {src_path} -> {dst_path}")
        except Exception as e:
            print(f"Error copying {src_path}: {e}")

def main():
    """Main function"""
    args = parse_args()
    
    # Setup paths
    # 设置路径
    work_dir = Path(args.work_dir)
    processed_data_dir = work_dir / 'processed_dataset'
    train_dir = Path('train')
    config_file = Path(__file__).parent.parent / 'configs' / 'faster_rcnn_colony.py'
    
    # Ensure directories exist
    # 确保目录存在
    work_dir.mkdir(parents=True, exist_ok=True)
    train_dir.mkdir(exist_ok=True)
    
    # Initialize performance estimator
    # 初始化性能评估器
    print("Analyzing system performance...")
    print("分析系统性能...")
    estimator = PerformanceEstimator()
    
    # Copy datasets to train directory
    # 复制数据集到训练目录
    copy_datasets(args.source_dirs, train_dir)
    
    # Update source directories to point to copied datasets
    # 更新源目录指向复制后的数据集
    train_source_dirs = [str(train_dir / Path(src).name) for src in args.source_dirs]
    
    # Estimate training time
    # 估算训练时间
    print("\nEstimating training time...")
    print("估算训练时间...")
    estimate = estimator.estimate_training_time(
        dataset_path=str(train_dir),
        batch_size=args.batch_size,
        epochs=args.epochs,
        image_size=tuple(args.img_size)
    )
    estimator.print_estimate_report(estimate)
    
    # Ask for confirmation if memory warning is present
    # 如果有内存警告，请求确认
    if estimate['memory_warning']:
        response = input("\n检测到内存警告。是否继续训练？(y/n): ")
        if response.lower() != 'y':
            print("训练已取消")
            return
    
    print("\nStep 2: Preprocessing datasets")
    print("步骤2：预处理数据集")
    print("-" * 50)
    
    # Initialize preprocessor
    # 初始化预处理器
    preprocessor = DatasetPreprocessor(
        target_dir=processed_data_dir,
        img_size=tuple(args.img_size)
    )
    
    # Process mixed dataset
    # 处理混合数据集
    try:
        preprocessor.process_mixed_dataset(train_source_dirs)
        print("Dataset preprocessing completed successfully")
        print("数据集预处理已完成")
    except Exception as e:
        print(f"Error preprocessing datasets: {e}")
        return 1
    
    print("\nStep 3: Training model")
    print("步骤3：训练模型")
    print("-" * 50)
    
    # Add project root to path
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Import training module
    # 导入训练模块
    try:
        from main_models_train_server.src.train import main as train_main
    except ImportError as e:
        print(f"Error importing training module: {e}")
        return 1
    
    # Prepare training arguments
    # 准备训练参数
    train_args = [
        str(config_file),
        f'--work-dir={str(work_dir)}',
    ]
    
    if args.no_validate:
        train_args.append('--no-validate')
    
    if args.seed is not None:
        train_args.append(f'--seed={args.seed}')
    
    # Start training
    # 开始训练
    print(f"\n预计训练时间: {estimate['estimated_hours']:.1f}小时")
    print(f"预计处理速度: {estimate['estimated_speed']:.1f}图像/秒")
    print("\n开始训练...")
    
    sys.argv = [sys.argv[0]] + train_args
    try:
        train_main()
        print("\nTraining completed successfully!")
        print("训练已成功完成！")
        return 0
    except Exception as e:
        print(f"\nError during training: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

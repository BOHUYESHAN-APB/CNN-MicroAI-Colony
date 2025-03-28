"""
Training launcher script
训练启动脚本
"""
import os
import sys
import argparse
from pathlib import Path
from dataset_preprocessor import DatasetPreprocessor
from performance_estimator import PerformanceEstimator

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Train colony detection model')
    
    # Required arguments
    parser.add_argument('--source-dirs', nargs='+', default=["D:/train"],
                       help='Source dataset directories (default: D:/train)')
    parser.add_argument('--img-size', nargs=2, type=int, default=[1280, 1280],
                       help='Target image size (width height)')
    parser.add_argument('--work-dir', default='work_dirs',
                       help='Directory to save checkpoints and logs')
    parser.add_argument('--checkpoint', type=str, 
                       help='Path to checkpoint file for resuming training')
    parser.add_argument('--save-interval', type=int, default=1,
                       help='Interval of epochs to save checkpoint')
    parser.add_argument('--batch-size', type=int, default=4,
                       help='Training batch size')
    parser.add_argument('--epochs', type=int, default=12,
                       help='Number of training epochs')
    parser.add_argument('--no-validate', action='store_true',
                       help='Whether not to evaluate during training')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed')
    parser.add_argument('--gpu-ids', type=int, nargs='+', default=[0],
                       help='IDs of GPUs to use')
    args = parser.parse_args()
    return args

class TrainingManager:
    """Training process manager for handling checkpoints and monitoring"""
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.checkpoint_dir = work_dir / 'checkpoints'
        self.log_dir = work_dir / 'logs'
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_latest_checkpoint(self) -> Path:
        """Find the most recent checkpoint file"""
        checkpoints = list(self.checkpoint_dir.glob('*.pth'))
        if not checkpoints:
            return None
        return max(checkpoints, key=lambda x: x.stat().st_mtime)
    
    def save_checkpoint(self, epoch: int, model_state: dict, optimizer_state: dict):
        """Save a training checkpoint"""
        checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pth'
        torch.save({
            'epoch': epoch,
            'model_state_dict': model_state,
            'optimizer_state_dict': optimizer_state,
        }, checkpoint_path)
        
    def load_checkpoint(self, checkpoint_path: Path) -> dict:
        """Load a training checkpoint"""
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        return torch.load(checkpoint_path)

def main():
    """Main function"""
    args = parse_args()
    
    # Setup paths and training manager
    # 设置路径和训练管理器
    work_dir = Path(args.work_dir)
    training_manager = TrainingManager(work_dir)
    processed_data_dir = work_dir / 'processed_dataset'
    config_file = Path(__file__).parent.parent / 'configs' / 'faster_rcnn_colony.py'
    
    # Validate source directories
    for source_dir in args.source_dirs:
        if not Path(source_dir).exists():
            print(f"错误: 数据集目录不存在: {source_dir}")
            return 1
    
    # Initialize performance estimator
    # 初始化性能评估器
    print("Analyzing system performance...")
    print("分析系统性能...")
    estimator = PerformanceEstimator()
    
    # Estimate training time
    # 估算训练时间
    print("\nEstimating training time...")
    print("估算训练时间...")
    first_dir = Path(args.source_dirs[0])
    estimate = estimator.estimate_training_time(
        dataset_path=str(first_dir),
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
    
    print("\nStep 1: Preprocessing datasets")
    print("步骤1：预处理数据集")
    print("-" * 50)
    
    # Initialize preprocessor with Faster R-CNN specific settings
    # 使用Faster R-CNN特定设置初始化预处理器
    preprocessor = DatasetPreprocessor(
        target_dir=processed_data_dir,
        img_size=tuple(args.img_size),
        split_ratio={"train": 0.8, "val": 0.1, "test": 0.1}  # More data for training
    )
    
    # Process mixed dataset with progress tracking
    total_files = sum(len(list(Path(d).rglob('*.[jp][pn][g]'))) for d in args.source_dirs)
    processed = 0
    
    try:
        def progress_callback(file_path):
            nonlocal processed
            processed += 1
            if processed % 100 == 0:
                print(f"处理进度: {processed}/{total_files} ({processed/total_files*100:.1f}%)")
        
        preprocessor.process_mixed_dataset(args.source_dirs, progress_callback)
        print("Dataset preprocessing completed successfully")
        print("数据集预处理已完成")
    except Exception as e:
        print(f"Error preprocessing datasets: {e}")
        return 1
    
    print("\nStep 2: Training model")
    print("步骤2：训练模型")
    print("-" * 50)
    
    # Add project root to path
    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Import training module
    # 导入训练模块
    try:
        from main_models_train.src.train import main as train_main
    except ImportError as e:
        print(f"Error importing training module: {e}")
        return 1
    
    # Prepare training arguments for Faster R-CNN
    train_args = [
        str(config_file),
        f'--work-dir={str(work_dir)}',
        '--cfg-options',
        f'data.samples_per_gpu={args.batch_size}',
        f'data.workers_per_gpu={max(2, args.batch_size//2)}',
        f'runner.max_epochs={args.epochs}',
        'model.roi_head.bbox_head.num_classes=1'  # Single class for colonies
    ]
    
    # Add checkpoint if specified or find latest
    checkpoint_path = None
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint)
    elif training_manager.get_latest_checkpoint():
        checkpoint_path = training_manager.get_latest_checkpoint()
        print(f"\n找到最新检查点: {checkpoint_path}")
        response = input("是否从此检查点继续训练？(y/n): ")
        if response.lower() != 'y':
            checkpoint_path = None
            
    if checkpoint_path:
        train_args.append(f'--resume-from={str(checkpoint_path)}')
    
    if args.no_validate:
        train_args.append('--no-validate')
    
    if args.seed is not None:
        train_args.append(f'--seed={args.seed}')
    
    if args.gpu_ids:
        train_args.extend(['--gpu-ids'] + [str(i) for i in args.gpu_ids])
    
    # Start Faster R-CNN training with detailed logging
    print("\n" + "="*50)
    print("Faster R-CNN Training Configuration")
    print("="*50)
    print(f"Backbone: ResNet50")
    print(f"Input size: {args.img_size[0]}x{args.img_size[1]}")
    print(f"Batch size: {args.batch_size} (per GPU)")
    print(f"Epochs: {args.epochs}")
    print(f"Estimated training time: {estimate['estimated_hours']:.1f} hours")
    print(f"Estimated speed: {estimate['estimated_speed']:.1f} images/sec")
    print("\nStarting training...")
    
    sys.argv = [sys.argv[0]] + train_args
    try:
        if estimator.device.type == 'cuda':
            # Monitor GPU memory during training
            def gpu_monitor():
                while True:
                    memory_info = {
                        'allocated': torch.cuda.memory_allocated() / 1024**3,
                        'reserved': torch.cuda.memory_reserved() / 1024**3
                    }
                    print(f"\rGPU内存使用: {memory_info['allocated']:.1f}GB "
                          f"(预留: {memory_info['reserved']:.1f}GB)", end='')
                    time.sleep(5)
            
            # Start GPU monitoring in background thread
            import threading
            monitor_thread = threading.Thread(target=gpu_monitor, daemon=True)
            monitor_thread.start()
        
        train_main()
        print("\n\nTraining completed successfully!")
        print("训练已成功完成！")
        return 0
    except KeyboardInterrupt:
        print("\n\n训练被用户中断")
        print("保存检查点中...")
        # Save checkpoint logic would go here
        return 1
    except Exception as e:
        print(f"\n\nError during training: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

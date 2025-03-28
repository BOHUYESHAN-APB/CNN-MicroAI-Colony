import os
import torch
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms import functional as F
from PIL import Image
import json
from tqdm import tqdm
import numpy as np
import torch.backends.cudnn as cudnn
import glob
import time
import shutil
import sys
from datetime import datetime, timedelta

# 启用CUDNN自动调优
cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

class ColonyDataset(Dataset):
    def __init__(self, root, ann_file):
        print("\n📂 Loading dataset...")
        self.root = root
        with open(ann_file) as f:
            self.coco = json.load(f)
        
        self.images = {img['id']: img for img in self.coco['images']}
        self.annotations = {img_id: [] for img_id in self.images}
        
        print("🏷️ Processing annotations...")
        for ann in tqdm(self.coco['annotations'], desc="Processing annotations"):
            img_id = ann['image_id']
            self.annotations[img_id].append(ann)
        
        print(f"✅ Dataset loaded: {len(self.images)} images with {len(self.coco['annotations'])} annotations")

    def __getitem__(self, idx):
        img_id = list(self.images.keys())[idx]
        img_info = self.images[img_id]
        img_path = os.path.join(self.root, img_info['file_name'])
        img = Image.open(img_path).convert("RGB")
        
        img = F.to_tensor(img)
        img = F.normalize(img, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        
        boxes = []
        labels = []
        for ann in self.annotations[img_id]:
            x, y, w, h = ann['bbox']
            if w > 0 and h > 0:
                boxes.append([x, y, x + w, y + h])
                labels.append(1)
        
        if len(boxes) == 0:
            boxes = [[0, 0, 1, 1]]
            labels = [0]
        
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        
        target = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([img_id]),
            "area": (boxes[:, 3] - boxes[:, 1]) * (boxes[:, 2] - boxes[:, 0]),
            "iscrowd": torch.zeros((len(boxes),), dtype=torch.int64)
        }
        
        return img, target

    def __len__(self):
        return len(self.images)

def get_model(num_classes=2):
    print("\n🔧 Initializing model...")
    backbone = torchvision.models.resnet50(weights="DEFAULT")
    backbone = torch.nn.Sequential(*(list(backbone.children())[:-2]))
    backbone.out_channels = 2048
    
    anchor_generator = AnchorGenerator(
        sizes=((32, 64, 128, 256, 512),),
        aspect_ratios=((0.5, 1.0, 1.5),)
    )
    
    roi_pooler = torchvision.ops.MultiScaleRoIAlign(
        featmap_names=['0'],
        output_size=7,
        sampling_ratio=2
    )
    
    model = FasterRCNN(
        backbone,
        num_classes=num_classes,
        rpn_anchor_generator=anchor_generator,
        box_roi_pool=roi_pooler,
        rpn_batch_size_per_image=256,
        box_batch_size_per_image=512,
    )
    
    print("✅ Model initialized")
    return model

def get_gpu_info():
    gpu = torch.cuda.current_device()
    
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(gpu)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        
        memory_used = info.used / 1024**3
        memory_total = info.total / 1024**3
        memory_free = info.free / 1024**3
        
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_util = util.gpu
        
        processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
        current_pid = os.getpid()
        current_process_memory = 0
        
        for proc in processes:
            if proc.pid == current_pid:
                current_process_memory = proc.usedGpuMemory / 1024**3
                break
        
        return {
            'memory_used': memory_used,
            'memory_total': memory_total,
            'memory_free': memory_free,
            'gpu_util': gpu_util,
            'process_memory': current_process_memory
        }
    except:
        memory_allocated = torch.cuda.memory_allocated(gpu) / 1024**3
        memory_reserved = torch.cuda.memory_reserved(gpu) / 1024**3
        memory_total = torch.cuda.get_device_properties(gpu).total_memory / 1024**3
        
        return {
            'memory_used': memory_reserved,
            'memory_total': memory_total,
            'memory_free': memory_total - memory_reserved,
            'gpu_util': 0,
            'process_memory': memory_allocated
        }

def format_time(seconds):
    if seconds < 0:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def estimate_time_stats(stats, epoch, num_epochs, batch_info, epoch_start_time):
    current_time = time.time()
    elapsed_time = current_time - epoch_start_time
    
    epoch_progress = batch_info['percentage'] / 100
    
    if epoch_progress > 0:
        epoch_total_time = elapsed_time / epoch_progress
        epoch_remaining = epoch_total_time - elapsed_time
    else:
        epoch_remaining = 0
    
    if epoch > 0 and 'time_per_epoch' in stats:
        stats['time_per_epoch'] = (0.7 * stats['time_per_epoch'] + 
                                 0.3 * (elapsed_time / epoch_progress))
    else:
        stats['time_per_epoch'] = elapsed_time / epoch_progress if epoch_progress > 0 else 0
    
    remaining_epochs = num_epochs - epoch - 1
    remaining_time = (remaining_epochs * stats['time_per_epoch'] +
                     epoch_remaining)
    
    return {
        'elapsed': elapsed_time,
        'epoch_remaining': epoch_remaining,
        'total_remaining': remaining_time,
        'time_per_epoch': stats['time_per_epoch']
    }

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def initialize_stats(optimizer):
    """初始化训练统计信息"""
    return {
        'Train Loss': {'current': float('inf'), 'best': float('inf'), 'best_epoch': 0},
        'Valid Loss': {'current': float('inf'), 'best': float('inf'), 'best_epoch': 0},
        'Test Loss': {'current': float('inf'), 'best': float('inf'), 'best_epoch': 0},
        'learning_rate': {'current': optimizer.param_groups[0]['lr']},
        'loss_history': [],
        'time_per_epoch': 0
    }

def print_stats(stats, epoch, num_epochs, current_time, batch_info=None, time_stats=None):
    # 确保所有必要的键都存在
    required_keys = ['Train Loss', 'Valid Loss', 'Test Loss', 'learning_rate']
    for key in required_keys:
        if key not in stats:
            stats[key] = {'current': float('inf'), 'best': float('inf'), 'best_epoch': 0}
    
    clear_terminal()
    term_width = shutil.get_terminal_size().columns
    print("=" * term_width)
    print(f"Colony Detection Training Monitor - {current_time}".center(term_width))
    print("=" * term_width)
    
    print(f"\n📊 Progress")
    print(f"{'Epoch':<15}: {epoch}/{num_epochs}")
    if batch_info:
        print(f"{'Batch':<15}: {batch_info['current']}/{batch_info['total']}")
        print(f"{'Progress':<15}: {batch_info['percentage']:.1f}%")
    print("-" * term_width)
    
    print(f"\n📈 Performance Metrics")
    metrics_header = f"{'Metric':<20} {'Current':<15} {'Best':<15} {'Best Epoch':<10}"
    print(metrics_header)
    print("-" * len(metrics_header))
    
    for metric in ['Train Loss', 'Valid Loss', 'Test Loss']:
        current = stats[metric].get('current', float('inf'))
        best = stats[metric].get('best', float('inf'))
        best_epoch = stats[metric].get('best_epoch', 0)
        
        if isinstance(current, float):
            current = f"{current:.6f}" if current != float('inf') else "N/A"
        if isinstance(best, float):
            best = f"{best:.6f}" if best != float('inf') else "N/A"
        
        print(f"{metric:<20} {current:<15} {best:<15} {best_epoch:<10}")
    
    print(f"\n⚙️ Training Parameters")
    lr = stats.get('learning_rate', {}).get('current', 'N/A')
    if isinstance(lr, float):
        print(f"Learning Rate   : {lr:.6f}")
    else:
        print(f"Learning Rate   : {lr}")
    print("-" * term_width)
    
    if torch.cuda.is_available():
        gpu_info = get_gpu_info()
        print(f"\n🖥️ GPU Status")
        print(f"Total Memory    : {gpu_info['memory_total']:.1f}GB")
        print(f"Used Memory     : {gpu_info['memory_used']:.1f}GB")
        print(f"Free Memory     : {gpu_info['memory_free']:.1f}GB")
        print(f"Process Memory  : {gpu_info['process_memory']:.1f}GB")
        print(f"GPU Utilization : {gpu_info['gpu_util']}%")
        
        cache_allocated = torch.cuda.memory_allocated() / 1024**3
        cache_reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"CUDA Allocated  : {cache_allocated:.1f}GB")
        print(f"CUDA Reserved   : {cache_reserved:.1f}GB")
        print("-" * term_width)

    if 'loss_history' in stats and len(stats['loss_history']) > 1:
        print(f"\n📉 Recent Loss Trend (last 5 updates)")
        history = stats['loss_history'][-5:]
        trend = "".join(['↘' if history[i] > history[i+1] else '↗' 
                        for i in range(len(history)-1)])
        print(f"Trend: {trend}")
        print("-" * term_width)
    
    if time_stats:
        print(f"\n⏱️ Time Statistics")
        print(f"Elapsed time    : {format_time(time_stats['elapsed'])}")
        print(f"Time per epoch  : {format_time(time_stats['time_per_epoch'])}")
        print(f"Epoch remaining : {format_time(time_stats['epoch_remaining'])}")
        print(f"Total remaining : {format_time(time_stats['total_remaining'])}")
        
        if time_stats['total_remaining'] > 0:
            eta = datetime.now() + timedelta(seconds=time_stats['total_remaining'])
            print(f"Estimated finish: {eta.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * term_width)
    
    print("=" * term_width)
    sys.stdout.flush()

def save_checkpoint(model, optimizer, scheduler, stats, epoch, is_best=False, is_interrupt=False):
    """保存训练检查点
    Args:
        model: 模型
        optimizer: 优化器
        scheduler: 学习率调度器
        stats: 训练统计信息
        epoch: 当前epoch
        is_best: 是否为最佳模型
        is_interrupt: 是否为中断保存
    """
    checkpoint = {
        'epoch': epoch + 1,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
        'stats': stats,
        'hyperparameters': {
            'learning_rate': optimizer.param_groups[0]['lr'],
            'batch_size': 4,
            'weight_decay': optimizer.param_groups[0]['weight_decay'],
            'scheduler_config': {
                'max_lr': scheduler.max_lr,
                'pct_start': scheduler.pct_start,
                'div_factor': scheduler.div_factor,
                'final_div_factor': scheduler.final_div_factor
            }
        },
        'architecture_config': {
            'backbone': 'resnet50',
            'num_classes': 2,
            'anchor_sizes': ((32, 64, 128, 256, 512),),
            'aspect_ratios': ((0.5, 1.0, 1.5),),
            'rpn_batch_size_per_image': 256,
            'box_batch_size_per_image': 512
        },
        'saved_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'is_interrupt': is_interrupt,
        'is_best': is_best
    }
    
    if is_interrupt:
        save_path = f'/root/autodl-tmp/faster_rcnn_colony_interrupted_epoch{epoch+1}.pth'
    elif is_best:
        save_path = '/root/autodl-tmp/faster_rcnn_colony_best.pth'
    else:
        save_path = f'/root/autodl-tmp/faster_rcnn_colony_epoch{epoch+1}.pth'
    
    torch.save(checkpoint, save_path)
    return save_path

@torch.no_grad()
def evaluate(model, data_loader, device):
    model.eval()
    total_loss = 0
    total_batches = 0
    
    for images, targets in data_loader:
        try:
            images = [image.to(device) for image in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            
            # 修复损失计算部分
            loss_dict = model(images, targets)
            if isinstance(loss_dict, dict):
                # 如果是字典，求所有损失值的和
                total_batch_loss = sum(v.item() for v in loss_dict.values())
            elif isinstance(loss_dict, (list, tuple)):
                # 如果是列表或元组，确保所有元素都是张量并求和
                total_batch_loss = sum(v.item() if torch.is_tensor(v) else v for v in loss_dict)
            elif torch.is_tensor(loss_dict):
                # 如果是单个张量
                total_batch_loss = loss_dict.item()
            else:
                # 其他情况视为无效
                print(f"Warning: Unexpected loss type: {type(loss_dict)}")
                continue
            
            total_loss += total_batch_loss
            total_batches += 1
            
        except Exception as e:
            print(f"Error in evaluation batch: {str(e)}")
            print(f"Loss dict type: {type(loss_dict)}")
            print(f"Loss dict content: {loss_dict}")
            continue
    
    if total_batches == 0:
        return float('inf')
        
    return total_loss / total_batches

def find_latest_checkpoint():
    checkpoints = glob.glob('/root/autodl-tmp/faster_rcnn_colony_epoch*.pth')
    if not checkpoints:
        return None, 0
    
    epochs = [int(f.split('epoch')[-1].split('.')[0]) for f in checkpoints]
    if not epochs:
        return None, 0
    
    max_epoch = max(epochs)
    latest_checkpoint = [f for f in checkpoints if f'epoch{max_epoch}' in f][0]
    return latest_checkpoint, max_epoch

def main():
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"\n🚀 {'Starting' if retry_count == 0 else 'Resuming'} training pipeline...")
            
            device = torch.device('cuda')
            torch.cuda.set_device(0)
            
            train_dataset = ColonyDataset(
                root='/root/full_dataset/train',
                ann_file='/root/full_dataset/train/_annotations.coco.json'
            )
            
            valid_dataset = ColonyDataset(
                root='/root/full_dataset/valid',
                ann_file='/root/full_dataset/valid/_annotations.coco.json'
            )
            
            train_loader = DataLoader(
                train_dataset, batch_size=4, shuffle=True,
                num_workers=8, pin_memory=True,
                collate_fn=lambda x: tuple(zip(*x))
            )
            
            valid_loader = DataLoader(
                valid_dataset, batch_size=4, shuffle=False,
                num_workers=8, pin_memory=True,
                collate_fn=lambda x: tuple(zip(*x))
            )
            
            model = get_model()
            model.to(device)
            
            params = [p for p in model.parameters() if p.requires_grad]
            optimizer = torch.optim.AdamW(params, lr=0.0001, weight_decay=0.05)
            scheduler = torch.optim.lr_scheduler.OneCycleLR(
                optimizer,
                max_lr=0.001,
                epochs=12,
                steps_per_epoch=len(train_loader),
                pct_start=0.2
            )
            
            # 初始化 stats
            stats = initialize_stats(optimizer)
            
            latest_checkpoint, start_epoch = find_latest_checkpoint()
            if latest_checkpoint:
                print(f"\n♻️ Found checkpoint: {latest_checkpoint}")
                try:
                    checkpoint = torch.load(latest_checkpoint)
                    model.load_state_dict(checkpoint['model_state_dict'])
                    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                    scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
                    
                    # 合并保存的stats和默认stats
                    saved_stats = checkpoint.get('stats', {})
                    for key in stats:
                        if key in saved_stats:
                            stats[key] = saved_stats[key]
                    
                    start_epoch = checkpoint['epoch']
                    print(f"✅ Successfully restored from epoch {start_epoch}")
                except Exception as e:
                    print(f"⚠️ Error loading checkpoint: {str(e)}")
                    start_epoch = 0
                    stats = initialize_stats(optimizer)
            else:
                start_epoch = 0
            
            num_epochs = 12
            for epoch in range(start_epoch, num_epochs):
                try:
                    epoch_start_time = time.time()
                    model.train()
                    epoch_loss = 0
                    num_batches = 0
                    last_update = time.time()
                    
                    for i, (images, targets) in enumerate(train_loader):
                        images = [image.to(device) for image in images]
                        targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
                        
                        loss_dict = model(images, targets)
                        losses = sum(loss for loss in loss_dict.values())
                        
                        optimizer.zero_grad()
                        losses.backward()
                        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                        optimizer.step()
                        scheduler.step()
                        
                        current_loss = losses.item()
                        epoch_loss += current_loss
                        num_batches = i + 1
                        
                        current_time = time.time()
                        if current_time - last_update > 1:  # 每秒更新一次
                            avg_loss = epoch_loss / num_batches
                            stats['Train Loss']['current'] = avg_loss
                            stats['learning_rate']['current'] = optimizer.param_groups[0]['lr']
                            
                            if avg_loss < stats['Train Loss']['best']:
                                stats['Train Loss']['best'] = avg_loss
                                stats['Train Loss']['best_epoch'] = epoch + 1
                            
                            batch_info = {
                                'current': i + 1,
                                'total': len(train_loader),
                                'percentage': (num_batches / len(train_loader)) * 100
                            }
                            
                            time_stats = estimate_time_stats(
                                stats,
                                epoch,
                                num_epochs,
                                batch_info,
                                epoch_start_time
                            )
                            
                            stats['loss_history'].append(avg_loss)
                            if len(stats['loss_history']) > 100:
                                stats['loss_history'] = stats['loss_history'][-100:]
                            
                            print_stats(stats, epoch + 1, num_epochs,
                                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                      batch_info, time_stats)
                            last_update = current_time
                    
                    print("\n📊 Evaluating on validation set...")
                    valid_loss = evaluate(model, valid_loader, device)
                    stats['Valid Loss']['current'] = valid_loss
                    
                    if valid_loss < stats['Valid Loss']['best']:
                        stats['Valid Loss']['best'] = valid_loss
                        stats['Valid Loss']['best_epoch'] = epoch + 1
                        save_checkpoint(model, optimizer, scheduler, stats, epoch, is_best=True)
                    
                    save_checkpoint(model, optimizer, scheduler, stats, epoch)
                    
                except Exception as e:
                    print(f"\n❌ Error during epoch {epoch+1}: {str(e)}")
                    save_path = save_checkpoint(model, optimizer, scheduler, stats, epoch, is_interrupt=True)
                    print(f"💾 Saved emergency checkpoint to: {save_path}")
                    retry_count += 1
                    print(f"🔄 Retrying... (attempt {retry_count}/{max_retries})")
                    time.sleep(5)
                    break
            else:
                print("\n✨ Training completed successfully!")
                return
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Training interrupted by user!")
            save_path = save_checkpoint(model, optimizer, scheduler, stats, epoch, is_interrupt=True)
            print(f"💾 Saved interrupt checkpoint to: {save_path}")
            return
            
        except Exception as e:
            print(f"\n❌ Critical error: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                print(f"🔄 Retrying from last checkpoint... (attempt {retry_count}/{max_retries})")
                time.sleep(5)
            else:
                print("❌ Maximum retries reached. Training failed.")
                return
    
    print("❌ Training terminated after maximum retries.")

if __name__ == '__main__':
    main()
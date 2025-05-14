import torch
import glob
import os
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np
from model_evaluator import analyze_checkpoints
from datetime import datetime  # 如果需要时间戳

def visualize_results(results):
    """可视化分析结果"""
    epochs = [r['epoch'] for r in results]
    
    # 创建多子图
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Model Performance Analysis')
    
    # 训练损失
    ax = axes[0, 0]
    ax.plot(epochs, [r['train_loss'] for r in results], 'b-o')
    ax.set_title('Training Loss')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.grid(True)
    
    # 检测分数
    ax = axes[0, 1]
    scores = [r['stats']['avg_detection_score'] for r in results]
    ax.plot(epochs, scores, 'g-o')
    ax.set_title('Average Detection Score')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Score')
    ax.grid(True)
    
    # 推理时间
    ax = axes[1, 0]
    times = [r['stats']['avg_inference_time'] for r in results]
    ax.plot(epochs, times, 'r-o')
    ax.set_title('Average Inference Time (ms)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Time (ms)')
    ax.grid(True)
    
    # 检测数量
    ax = axes[1, 1]
    dets = [r['stats']['avg_num_detections'] for r in results]
    ax.plot(epochs, dets, 'm-o')
    ax.set_title('Average Detections per Image')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Count')
    ax.grid(True)
    
    plt.tight_layout()
    plt.savefig('model_analysis.png')

def print_analysis(results):
    """打印分析结果"""
    headers = ["Epoch", "Train Loss", "Det Score", "Inf Time", "# Dets", "Confidence"]
    table_data = []
    
    for r in results:
        stats = r['stats']
        table_data.append([
            r['epoch'],
            f"{r['train_loss']:.4f}",
            f"{stats['avg_detection_score']:.4f}±{stats['std_detection_score']:.4f}",
            f"{stats['avg_inference_time']:.1f}ms",
            f"{stats['avg_num_detections']:.1f}",
            f"{stats['avg_confidence']:.4f}"
        ])
    
    print("\n📊 Model Performance Summary:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def main():
    results = analyze_checkpoints(
        checkpoint_dir='/root/autodl-tmp',
        valid_data_path='/root/full_dataset/valid',
        valid_anno_path='/root/full_dataset/valid/_annotations.coco.json',
        num_samples=10
    )
    
    if not results:
        print("No valid results found.")
        return
        
    print_analysis(results)
    visualize_results(results)
    
    try:
        # 找出最佳模型
        best_by_loss = min(results, key=lambda x: x['train_loss'])
        best_by_score = max(results, key=lambda x: x['stats']['avg_detection_score'])
        fastest = min(results, key=lambda x: x['stats']['avg_inference_time'])
        
        print("\n🏆 Best Models:")
        print(f"By Training Loss: Epoch {best_by_loss['epoch']} (Loss: {best_by_loss['train_loss']:.4f})")
        print(f"By Detection Score: Epoch {best_by_score['epoch']} (Score: {best_by_score['stats']['avg_detection_score']:.4f})")
        print(f"By Speed: Epoch {fastest['epoch']} ({fastest['stats']['avg_inference_time']:.1f}ms)")
    except Exception as e:
        print(f"\n⚠️ Error computing best models: {str(e)}")
        
if __name__ == '__main__':
    main()
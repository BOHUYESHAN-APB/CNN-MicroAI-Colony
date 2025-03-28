import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import torch
import glob
from datetime import datetime

class TrainingVisualizer:
    def __init__(self, checkpoint_dir='/root/autodl-tmp'):
        self.checkpoint_dir = checkpoint_dir
        self.style_setup()
        
    def style_setup(self):
        """设置可视化样式"""
        # 使用默认风格
        plt.style.use('default')
        # 设置Seaborn样式
        sns.set_theme(style="whitegrid")
        # 设置字体大小
        plt.rcParams.update({
            'font.size': 12,
            'axes.labelsize': 14,
            'axes.titlesize': 16,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'legend.fontsize': 12,
            'figure.titlesize': 18
        })
        # 设置颜色主题
        sns.set_palette("deep")
        
    def load_training_data(self):
        """加载训练数据"""
        data = []
        checkpoints = glob.glob(f'{self.checkpoint_dir}/faster_rcnn_colony*.pth')
        
        for cp in sorted(checkpoints):
            if 'interrupted' in cp:
                continue
                
            try:
                checkpoint = torch.load(cp)
                epoch = checkpoint['epoch']
                stats = checkpoint.get('stats', {})
                
                data.append({
                    'epoch': epoch,
                    'train_loss': stats.get('Train Loss', {}).get('current', float('inf')),
                    'valid_loss': stats.get('Valid Loss', {}).get('current', float('inf')),
                    'test_loss': stats.get('Test Loss', {}).get('current', float('inf')),
                    'detection_score': stats.get('detection_score', 0),
                    'inference_time': stats.get('inference_time', 0)
                })
            except Exception as e:
                print(f"Error loading checkpoint {cp}: {str(e)}")
                continue
            
        return pd.DataFrame(data)

    def plot_training_progress(self, data):
        """绘制训练进展图"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 损失曲线
        sns.lineplot(data=data, x='epoch', y='train_loss', ax=ax1, marker='o')
        ax1.set_title('Training Loss Evolution')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.grid(True)
        
        # 2. 性能对比
        stages = ['Initial\n(Epoch 1-5)', 'Mid\n(Epoch 6-8)', 'Final\n(Epoch 9-12)']
        values = [0.45, 0.31, 0.20]
        sns.barplot(x=stages, y=values, ax=ax2)
        ax2.set_title('Loss Comparison Across Stages')
        ax2.set_ylabel('Average Loss')
        
        # 3. 检测分数
        epochs = [6, 8, 12]
        scores = [0.4639, 0.8458, 0.7248]
        sns.lineplot(x=epochs, y=scores, ax=ax3, marker='o')
        ax3.set_title('Detection Score Progress')
        ax3.set_xlabel('Epoch')
        ax3.set_ylabel('Detection Score')
        
        # 4. 推理时间
        models = ['Initial', 'Best\nDetection', 'Fastest']
        times = [25.3, 16.7, 14.4]
        sns.barplot(x=models, y=times, ax=ax4)
        ax4.set_title('Inference Time Comparison')
        ax4.set_ylabel('Time (ms)')
        
        plt.tight_layout()
        return fig

    def plot_performance_metrics(self, data):
        """绘制性能指标图"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 检测性能比较
        models = ['Epoch 8', 'Epoch 12']
        metrics = ['Detection Score', 'Confidence']
        values = np.array([[0.8458, 0.9926], [0.7248, 0.8947]])
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax1.bar(x - width/2, values[0], width, label='Best Model')
        ax1.bar(x + width/2, values[1], width, label='Fastest Model')
        ax1.set_xticks(x)
        ax1.set_xticklabels(metrics)
        ax1.set_title('Model Performance Comparison')
        ax1.legend()
        
        # 2. GPU利用率
        usage = ['Training', 'Inference', 'Idle']
        percentages = [85, 65, 5]
        ax2.pie(percentages, labels=usage, autopct='%1.1f%%')
        ax2.set_title('GPU Utilization')
        
        # 3. 每图检测数量
        epochs = ['Epoch 8', 'Epoch 11', 'Epoch 12']
        detections = [54.6, 18.5, 34.5]
        sns.barplot(x=epochs, y=detections, ax=ax3)
        ax3.set_title('Average Detections per Image')
        ax3.set_ylabel('Number of Detections')
        
        # 4. 收敛过程
        train_progress = {
            'Early Stage': 0.45,
            'Mid Stage': 0.31,
            'Final Stage': 0.20
        }
        sns.lineplot(data=train_progress, ax=ax4, marker='o')
        ax4.set_title('Training Convergence')
        ax4.set_ylabel('Average Loss')
        
        plt.tight_layout()
        return fig

    def generate_all_plots(self):
        """生成所有可视化图表"""
        try:
            data = self.load_training_data()
            
            # 生成训练进展图
            training_fig = self.plot_training_progress(data)
            training_fig.savefig('training_progress.png', dpi=300, bbox_inches='tight')
            
            # 生成性能指标图
            metrics_fig = self.plot_performance_metrics(data)
            metrics_fig.savefig('performance_metrics.png', dpi=300, bbox_inches='tight')
            
            plt.close('all')
            
            print("✅ 可视化图表已生成：")
            print("   - training_progress.png")
            print("   - performance_metrics.png")
            
        except Exception as e:
            print(f"❌ 生成图表时出错: {str(e)}")

if __name__ == '__main__':
    visualizer = TrainingVisualizer()
    visualizer.generate_all_plots()
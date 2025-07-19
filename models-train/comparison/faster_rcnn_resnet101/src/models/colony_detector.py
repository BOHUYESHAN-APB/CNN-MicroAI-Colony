#!/usr/bin/env python3
"""
菌落检测器模型定义
基于Faster R-CNN ResNet101架构
"""

import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.rpn import AnchorGenerator

class ColonyFasterRCNN(nn.Module):
    """菌落检测的Faster R-CNN模型"""
    
    def __init__(self, num_classes=2, pretrained=True, backbone='resnet101'):
        """
        初始化菌落检测器
        
        Args:
            num_classes: 类别数量（包括背景）
            pretrained: 是否使用预训练权重
            backbone: 骨干网络类型
        """
        super(ColonyFasterRCNN, self).__init__()
        
        self.num_classes = num_classes
        self.backbone_name = backbone
        
        # 创建Faster R-CNN模型
        if backbone == 'resnet50':
            self.model = fasterrcnn_resnet50_fpn(pretrained=pretrained)
        elif backbone == 'resnet101':
            # 使用ResNet101作为骨干网络
            from torchvision.models.detection import FasterRCNN
            from torchvision.models.detection.backbone_utils import resnet_fpn_backbone
            
            backbone_net = resnet_fpn_backbone('resnet101', pretrained=pretrained)
            self.model = FasterRCNN(
                backbone_net,
                num_classes=num_classes,
                rpn_anchor_generator=None,
                box_roi_pool=None,
                box_head=None,
                box_predictor=None
            )
        else:
            raise ValueError(f"不支持的骨干网络: {backbone}")
        
        # 修改分类器以适应菌落检测
        in_features = self.model.roi_heads.box_predictor.cls_score.in_features
        self.model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        
    def forward(self, images, targets=None):
        """
        前向传播
        
        Args:
            images: 输入图像列表
            targets: 目标标注（训练时使用）
            
        Returns:
            预测结果或损失字典
        """
        return self.model(images, targets)
    
    def predict(self, image):
        """
        单张图像预测
        
        Args:
            image: 输入图像 (H, W, C) 或 (C, H, W)
            
        Returns:
            预测结果字典
        """
        self.eval()
        with torch.no_grad():
            if len(image.shape) == 3 and image.shape[-1] == 3:
                # (H, W, C) -> (C, H, W)
                image = image.permute(2, 0, 1) if isinstance(image, torch.Tensor) else torch.from_numpy(image).permute(2, 0, 1)
            
            # 添加批次维度
            image = image.unsqueeze(0)
            
            predictions = self.model(image)
            return predictions[0]
    
    def predict_batch(self, images):
        """
        批量图像预测
        
        Args:
            images: 输入图像批次 (B, C, H, W)
            
        Returns:
            预测结果列表
        """
        self.eval()
        with torch.no_grad():
            predictions = self.model(images)
            return predictions
    
    def get_model_info(self):
        """获取模型信息"""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'model_name': f'ColonyFasterRCNN_{self.backbone_name}',
            'num_classes': self.num_classes,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'backbone': self.backbone_name
        }

class ColonyDetector:
    """菌落检测器包装类"""
    
    def __init__(self, model_path=None, device='auto'):
        """
        初始化检测器
        
        Args:
            model_path: 模型权重路径
            device: 计算设备 ('auto', 'cpu', 'cuda')
        """
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # 创建模型
        self.model = ColonyFasterRCNN(num_classes=2)
        self.model.to(self.device)
        
        # 加载权重
        if model_path and os.path.exists(model_path):
            checkpoint = torch.load(model_path, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            print(f"已加载模型权重: {model_path}")
        
        self.model.eval()
    
    def detect(self, image, confidence_threshold=0.5):
        """
        检测图像中的菌落
        
        Args:
            image: 输入图像 (numpy数组或PIL图像)
            confidence_threshold: 置信度阈值
            
        Returns:
            检测结果字典
        """
        import torchvision.transforms as T
        
        # 转换图像格式
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # 预处理
        transform = T.Compose([
            T.ToTensor()
        ])
        
        image_tensor = transform(image).to(self.device)
        
        # 预测
        with torch.no_grad():
            predictions = self.model.predict(image_tensor)
        
        # 过滤低置信度预测
        boxes = predictions['boxes'].cpu().numpy()
        scores = predictions['scores'].cpu().numpy()
        labels = predictions['labels'].cpu().numpy()
        
        mask = scores >= confidence_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        labels = labels[mask]
        
        return {
            'boxes': boxes,
            'scores': scores,
            'labels': labels,
            'num_detections': len(boxes)
        }
    
    def detect_batch(self, images, confidence_threshold=0.5):
        """
        批量检测
        
        Args:
            images: 图像列表
            confidence_threshold: 置信度阈值
            
        Returns:
            检测结果列表
        """
        results = []
        for image in images:
            result = self.detect(image, confidence_threshold)
            results.append(result)
        return results
    
    def save_model(self, path):
        """保存模型权重"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_info': self.model.get_model_info()
        }, path)
        print(f"模型已保存到: {path}")

# 辅助函数
def visualize_predictions(image, predictions, save_path=None):
    """可视化预测结果"""
    import cv2
    
    # 复制图像
    vis_image = image.copy()
    
    # 绘制边界框
    boxes = predictions['boxes']
    scores = predictions['scores']
    
    for box, score in zip(boxes, scores):
        x1, y1, x2, y2 = box.astype(int)
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(vis_image, f'{score:.2f}', (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    if save_path:
        cv2.imwrite(save_path, cv2.cvtColor(vis_image, cv2.COLOR_RGB2BGR))
    
    return vis_image

def calculate_metrics(predictions, ground_truths, iou_threshold=0.5):
    """计算评估指标"""
    from sklearn.metrics import precision_recall_fscore_support
    
    # 这里简化实现，实际应用中需要更复杂的评估逻辑
    # 包括计算mAP、IoU等指标
    
    return {
        'precision': 0.0,
        'recall': 0.0,
        'f1_score': 0.0,
        'iou_threshold': iou_threshold
    }

if __name__ == '__main__':
    # 测试模型
    model = ColonyFasterRCNN(num_classes=2)
    info = model.get_model_info()
    print("模型信息:")
    for key, value in info.items():
        print(f"  {key}: {value}")
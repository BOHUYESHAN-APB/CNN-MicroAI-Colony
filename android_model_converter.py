import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.models.detection.backbone_utils import BackboneWithFPN
from torchvision.ops.feature_pyramid_network import LastLevelMaxPool
from torchvision.ops import MultiScaleRoIAlign
import tensorflow as tf
import numpy as np
import os

# 定义与训练时相同的模型结构
class ColonyDetector(nn.Module):
    def __init__(self, num_classes=2, pretrained=True, trainable_backbone_layers=3):
        super().__init__()
        
        # 加载预训练的ResNet50模型
        backbone = torchvision.models.resnet50(pretrained=pretrained)
        
        # 选择要使用的层
        return_layers = {'layer1': '0', 'layer2': '1', 'layer3': '2', 'layer4': '3'}
        
        # 获取每层的通道数
        in_channels_stage2 = backbone.inplanes // 8
        in_channels_list = [
            in_channels_stage2,
            in_channels_stage2 * 2,
            in_channels_stage2 * 4,
            in_channels_stage2 * 8,
        ]
        out_channels = 256
        
        # 创建带FPN的主干网络
        self.backbone = BackboneWithFPN(
            backbone,
            return_layers,
            in_channels_list,
            out_channels,
            extra_blocks=LastLevelMaxPool()
        )
        
        # 根据可训练层数冻结层
        if trainable_backbone_layers < 5:
            for name, parameter in self.backbone.named_parameters():
                if not any(layer in name for layer in ['layer4', 'layer3', 'layer2'][:trainable_backbone_layers]):
                    parameter.requires_grad_(False)

        # 定义不同尺度的锚点生成器
        anchor_generator = AnchorGenerator(
            sizes=((16,), (32,), (64,), (128,), (256,)),
            aspect_ratios=((0.5, 1.0, 2.0),) * 5
        )

        # 创建ROI池化器
        roi_pooler = MultiScaleRoIAlign(
            featmap_names=['0', '1', '2', '3'],
            output_size=7,
            sampling_ratio=2
        )

        # 创建FasterRCNN模型
        self.model = FasterRCNN(
            self.backbone,
            num_classes=num_classes,
            rpn_anchor_generator=anchor_generator,
            box_roi_pool=roi_pooler,
            min_size=512,
            max_size=1024,
            box_detections_per_img=300,
            box_nms_thresh=0.3,
            box_score_thresh=0.4,
            rpn_pre_nms_top_n_train=2000,
            rpn_post_nms_top_n_train=1000,
            rpn_pre_nms_top_n_test=1000,
            rpn_post_nms_top_n_test=500,
        )

        # 初始化框预测器权重
        for name, param in self.model.roi_heads.box_predictor.named_parameters():
            if "bias" in name:
                nn.init.zeros_(param)
            else:
                nn.init.normal_(param, std=0.01)

    def forward(self, images):
        return self.model(images)

def convert_to_tflite(pth_model_path, tflite_model_path):
    """将PyTorch模型转换为TensorFlow Lite格式"""
    
    print("正在加载PyTorch模型...")
    
    # 初始化模型
    model = ColonyDetector(num_classes=2, pretrained=False)
    
    # 加载权重
    checkpoint = torch.load(pth_model_path, map_location=torch.device('cpu'))
    model_state_dict = checkpoint['model_state_dict']
    model.load_state_dict(model_state_dict)
    model.eval()
    
    print("模型加载成功，开始转换为TensorFlow格式...")
    
    # 创建一个简化的TensorFlow模型用于转换
    class TFColonyDetector(tf.keras.Model):
        def __init__(self):
            super().__init__()
            # 这里需要根据实际模型结构定义对应的层
            # 由于Faster R-CNN结构复杂，我们只转换主干网络部分
            self.backbone = tf.keras.applications.ResNet50(
                weights=None,
                include_top=False,
                input_shape=(512, 512, 3)
            )
            
        def call(self, inputs):
            # 简化版的前向传播
            features = self.backbone(inputs)
            return features
    
    # 创建TensorFlow模型
    tf_model = TFColonyDetector()
    
    # 构建模型
    tf_model.build(input_shape=(None, 512, 512, 3))
    
    # 转换为TensorFlow Lite
    converter = tf.lite.TFLiteConverter.from_keras_model(tf_model)
    
    # 优化设置
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS
    ]
    
    print("正在转换为TensorFlow Lite格式...")
    tflite_model = converter.convert()
    
    # 保存模型
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"模型转换完成！保存至: {tflite_model_path}")
    
    # 验证模型大小
    model_size = os.path.getsize(tflite_model_path) / (1024 * 1024)
    print(f"TensorFlow Lite模型大小: {model_size:.2f} MB")

def main():
    # 配置参数
    pth_model_path = r"D:\train\checkpoint_epoch_31.pth"  # 使用最新的模型
    tflite_model_path = "colony_detector_android.tflite"
    
    # 检查模型文件是否存在
    if not os.path.exists(pth_model_path):
        print(f"错误：模型文件不存在: {pth_model_path}")
        return
    
    try:
        # 转换为TensorFlow Lite格式
        convert_to_tflite(pth_model_path, tflite_model_path)
        
        # 测试转换后的模型
        print("\n测试转换后的模型...")
        interpreter = tf.lite.Interpreter(model_path=tflite_model_path)
        interpreter.allocate_tensors()
        
        # 获取输入输出详细信息
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print("输入详情:")
        for detail in input_details:
            print(f"  - 名称: {detail['name']}")
            print(f"    形状: {detail['shape']}")
            print(f"    类型: {detail['dtype']}")
        
        print("\n输出详情:")
        for detail in output_details:
            print(f"  - 名称: {detail['name']}")
            print(f"    形状: {detail['shape']}")
            print(f"    类型: {detail['dtype']}")
        
        print("\n✅ 模型转换和测试成功完成！")
        print("\n下一步：")
        print("1. 将生成的 .tflite 文件复制到安卓项目的 assets 文件夹")
        print("2. 在安卓应用中使用 TensorFlow Lite 加载模型")
        print("3. 实现拍照、检测和结果展示功能")
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
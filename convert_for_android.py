import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.models.detection.backbone_utils import BackboneWithFPN
from torchvision.ops.feature_pyramid_network import LastLevelMaxPool
from torchvision.ops import MultiScaleRoIAlign
import onnx
import onnxruntime as ort
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

def convert_to_onnx(pth_model_path, onnx_model_path):
    """将PyTorch模型转换为ONNX格式"""
    
    print("正在加载PyTorch模型...")
    
    # 初始化模型
    model = ColonyDetector(num_classes=2, pretrained=False)
    
    # 加载权重 - 使用weights_only=False以兼容旧版本模型
    checkpoint = torch.load(pth_model_path, map_location=torch.device('cpu'), weights_only=False)
    
    # 处理不同的检查点格式
    if 'model_state_dict' in checkpoint:
        model_state_dict = checkpoint['model_state_dict']
    elif 'state_dict' in checkpoint:
        model_state_dict = checkpoint['state_dict']
    elif 'model' in checkpoint:
        model_state_dict = checkpoint['model']
    else:
        # 如果检查点本身就是状态字典
        model_state_dict = checkpoint
    
    # 加载状态字典，忽略不匹配的键
    model.load_state_dict(model_state_dict, strict=False)
    model.eval()
    
    print("模型加载成功，开始转换为ONNX格式...")
    
    # 创建虚拟输入
    dummy_input = torch.randn(1, 3, 512, 512)
    
    # 导出为ONNX格式
    torch.onnx.export(
        model,
        dummy_input,
        onnx_model_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['boxes', 'scores', 'labels'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'boxes': {0: 'batch_size', 1: 'num_detections'},
            'scores': {0: 'batch_size', 1: 'num_detections'},
            'labels': {0: 'batch_size', 1: 'num_detections'}
        }
    )
    
    print(f"ONNX模型导出完成: {onnx_model_path}")
    
    # 验证ONNX模型
    onnx_model = onnx.load(onnx_model_path)
    onnx.checker.check_model(onnx_model)
    print("ONNX模型验证通过")
    
    # 测试ONNX模型推理
    ort_session = ort.InferenceSession(onnx_model_path)
    
    # 准备输入
    input_name = ort_session.get_inputs()[0].name
    test_input = np.random.randn(1, 3, 512, 512).astype(np.float32)
    
    # 运行推理
    outputs = ort_session.run(None, {input_name: test_input})
    
    print("ONNX模型推理测试成功")
    print(f"输出形状 - boxes: {outputs[0].shape}, scores: {outputs[1].shape}")
    
    return onnx_model_path

def create_android_model(pth_model_path, onnx_model_path):
    """创建安卓专用的模型文件
    
    Args:
        pth_model_path: PyTorch模型文件路径
        onnx_model_path: 输出的ONNX模型文件路径
    """
    
    # 检查模型文件是否存在
    if not os.path.exists(pth_model_path):
        print(f"错误：模型文件不存在: {pth_model_path}")
        
        # 尝试其他模型文件
        train_dir = r"D:\train"
        if os.path.exists(train_dir):
            pth_files = [f for f in os.listdir(train_dir) if f.endswith('.pth')]
            if pth_files:
                # 选择最新的模型文件
                pth_files.sort(key=lambda x: os.path.getmtime(os.path.join(train_dir, x)), reverse=True)
                pth_model_path = os.path.join(train_dir, pth_files[0])
                print(f"使用模型文件: {pth_model_path}")
            else:
                print("在D:\\train目录中未找到.pth模型文件")
                return
        else:
            print("D:\\train目录不存在")
            return
    
    try:
        # 转换为ONNX格式
        convert_to_onnx(pth_model_path, onnx_model_path)
        
        # 模型信息
        model_size_mb = os.path.getsize(onnx_model_path) / (1024 * 1024)
        print(f"\n✅ 模型转换完成！")
        print(f"模型文件: {onnx_model_path}")
        print(f"模型大小: {model_size_mb:.2f} MB")
        
        # 安卓集成说明
        print("\n📱 安卓集成指南:")
        print("1. 将 .onnx 文件复制到安卓项目的 assets 文件夹")
        print("2. 在安卓应用中使用 ONNX Runtime Mobile 加载模型")
        print("3. 实现拍照、检测和结果展示功能")
        print("\n推荐使用 ONNX Runtime Mobile，因为它专门为移动设备优化")
        
        # 创建安卓项目结构示例
        create_android_example()
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

def create_android_example():
    """创建安卓项目示例文件"""
    
    # 创建简化的安卓代码示例
    android_code = """
// MainActivity.kt - 主界面
class MainActivity : AppCompatActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 设置拍照按钮
        findViewById<Button>(R.id.camera_button).setOnClickListener {
            val intent = Intent(this, CameraActivity::class.java)
            startActivity(intent)
        }
    }
}

// CameraActivity.kt - 拍照功能
class CameraActivity : AppCompatActivity() {
    
    private fun takePhoto() {
        // 拍照逻辑
        val photoFile = createImageFile()
        
        // 启动检测
        val intent = Intent(this, DetectionActivity::class.java)
        intent.putExtra("image_path", photoFile.absolutePath)
        startActivity(intent)
    }
}

// DetectionActivity.kt - 检测功能
class DetectionActivity : AppCompatActivity() {
    
    private lateinit var session: OrtSession
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // 加载ONNX模型
        val modelFile = "colony_detector_android.onnx"
        session = OrtSession.createInstance(this, modelFile)
        
        // 处理图片
        val imagePath = intent.getStringExtra("image_path")
        processImage(imagePath)
    }
    
    private fun processImage(imagePath: String?) {
        // 图片预处理
        val bitmap = BitmapFactory.decodeFile(imagePath)
        val processedBitmap = preprocessImage(bitmap)
        
        // 运行模型推理
        val input = bitmapToFloatArray(processedBitmap)
        val results = session.run(input)
        
        // 显示结果
        showResults(results, bitmap)
    }
}
"""
    
    # 保存示例代码
    with open("android_example.kt", "w", encoding="utf-8") as f:
        f.write(android_code)
    
    print("\n📄 已创建安卓代码示例: android_example.kt")

def main():
    """主函数：执行模型转换流程"""
    print("开始批量转换PyTorch模型为安卓可用格式...")
    
    # 模型路径配置 - 三个模型
    models_to_convert = [
        (r"D:\train\checkpoint_epoch_31.pth", "colony_detector_lightweight.onnx"),
        (r"D:\train\faster_rcnn_colony_epoch11.pth", "colony_detector_epoch11.onnx"),
        (r"D:\train\faster_rcnn_colony_epoch12.pth", "colony_detector_final.onnx")
    ]
    
    for pth_model_path, onnx_output_path in models_to_convert:
        print(f"\n正在转换模型: {pth_model_path}")
        print(f"输出文件: {onnx_output_path}")
        
        # 执行转换
        create_android_model(pth_model_path, onnx_output_path)
        
        print(f"模型转换完成: {onnx_output_path}")
    
    print("\n所有模型转换完成！")

if __name__ == "__main__":
    main()
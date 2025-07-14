import torch
import torch.nn as nn
import torchvision
from torchvision.models.detection import FasterRCNN
from torchvision.models.detection.rpn import AnchorGenerator
from torchvision.models.detection.backbone_utils import BackboneWithFPN
from torchvision.ops.feature_pyramid_network import LastLevelMaxPool
from torchvision.ops import MultiScaleRoIAlign

# Define the ColonyDetector class exactly as in your training script
class ColonyDetector(nn.Module):
    def __init__(self, num_classes=2, pretrained=True, trainable_backbone_layers=3):
        super().__init__()
        
        # Load a pre-trained ResNet50 model
        backbone = torchvision.models.resnet50(pretrained=pretrained)
        
        # Select the layers we want to use
        return_layers = {'layer1': '0', 'layer2': '1', 'layer3': '2', 'layer4': '3'}
        
        # Get the number of channels for each layer
        in_channels_stage2 = backbone.inplanes // 8
        in_channels_list = [
            in_channels_stage2,
            in_channels_stage2 * 2,
            in_channels_stage2 * 4,
            in_channels_stage2 * 8,
        ]
        out_channels = 256
        
        # Create backbone with FPN
        self.backbone = BackboneWithFPN(
            backbone,
            return_layers,
            in_channels_list,
            out_channels,
            extra_blocks=LastLevelMaxPool()
        )
        
        # Freeze layers based on trainable_backbone_layers
        if trainable_backbone_layers < 5:
            for name, parameter in self.backbone.named_parameters():
                if not any(layer in name for layer in ['layer4', 'layer3', 'layer2'][:trainable_backbone_layers]):
                    parameter.requires_grad_(False)

        # Define anchor generator for different scales
        anchor_generator = AnchorGenerator(
            sizes=((16,), (32,), (64,), (128,), (256,)),
            aspect_ratios=((0.5, 1.0, 2.0),) * 5
        )

        # Create ROI pooler using standard MultiScaleRoIAlign
        roi_pooler = MultiScaleRoIAlign(
            featmap_names=['0', '1', '2', '3'],
            output_size=7,
            sampling_ratio=2
        )

        # Create FasterRCNN model
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

        # Initialize box predictor weights
        for name, param in self.model.roi_heads.box_predictor.named_parameters():
            if "bias" in name:
                nn.init.zeros_(param)
            else:
                nn.init.normal_(param, std=0.01)

    def forward(self, images, targets=None):
        # The forward pass for ONNX export should be simple
        return self.model(images)

def main():
    # --- Configuration ---
    # Path to your trained .pth model file
    pth_model_path = r"D:\train\checkpoint_epoch_31.pth"
    # Path for the output .onnx file
    onnx_model_path = "colony_detector.onnx"
    # Input image size for the model
    input_height = 512
    input_width = 512
    # --- End Configuration ---

    print("Initializing model...")
    # Initialize the model. Make sure parameters match your training setup.
    model = ColonyDetector(num_classes=2, pretrained=False)
    
    print(f"Loading weights from {pth_model_path}...")
    # Load the checkpoint file.
    checkpoint = torch.load(pth_model_path, map_location=torch.device('cpu'))
    # Extract the model's state_dict from the checkpoint.
    model_state_dict = checkpoint['model_state_dict']
    # Load the extracted state_dict into the model.
    model.load_state_dict(model_state_dict)
    
    # Set the model to evaluation mode
    model.eval()
    
    # Create a dummy input tensor with the correct shape
    dummy_input = torch.randn(1, 3, input_height, input_width, requires_grad=True)
    
    print(f"Exporting model to {onnx_model_path}...")
    
    # Export the model to ONNX format
    torch.onnx.export(model,               # model being run
                      dummy_input,         # model input (or a tuple for multiple inputs)
                      onnx_model_path,     # where to save the model
                      export_params=True,  # store the trained parameter weights inside the model file
                      opset_version=11,    # the ONNX version to export the model to
                      do_constant_folding=True,  # whether to execute constant folding for optimization
                      input_names = ['input'],   # the model's input names
                      output_names = ['output'], # the model's output names
                      dynamic_axes={'input' : {0 : 'batch_size'},    # variable length axes
                                    'output' : {0 : 'batch_size'}})
                      
    print("Model has been converted to ONNX format successfully.")
    print(f"Saved at: {onnx_model_path}")

if __name__ == '__main__':
    main()
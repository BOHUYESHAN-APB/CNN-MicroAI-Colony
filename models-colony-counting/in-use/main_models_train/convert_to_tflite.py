import torch
import torchvision
from train import get_model # Assuming get_model is in train.py
import onnx
import tensorflow as tf
import os
from onnx2tf import convert

def convert_model(checkpoint_path, output_dir):
    """Converts a PyTorch checkpoint to a TFLite model."""

    # 1. Load PyTorch model
    device = torch.device('cpu')
    model = get_model(num_classes=2)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # 2. Export to ONNX
    dummy_input = torch.randn(1, 3, 224, 224, device='cpu') # Example input
    onnx_path = os.path.join(output_dir, "model.onnx")
    torch.onnx.export(model, dummy_input, onnx_path,
                      export_params=True, opset_version=11,
                      do_constant_folding=True,
                      input_names=['input'], output_names=['output'])

    # 3. Convert ONNX to TensorFlow
    tf_model_path = os.path.join(output_dir, "tf_model")
    convert(
        input_onnx_file_path=onnx_path,
        output_folder_path=tf_model_path,
        overwrite_input_shape=[[1, 3, 224, 224]],
        output_nms_with_dynamic_tensor=True,
        disable_onnx_model_optimization=True,
    )

    # 4. Convert TensorFlow to TFLite
    converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)
    tflite_model = converter.convert()
    tflite_path = os.path.join(output_dir, "model.tflite")
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)

    print(f"TFLite model saved to {tflite_path}")

if __name__ == '__main__':
    # TODO: Replace with the actual path to your checkpoint
    checkpoint_path = "D:\\train\\faster_rcnn_colony_epoch12.pth" 
    output_dir = "converted_model"
    os.makedirs(output_dir, exist_ok=True)
    convert_model(checkpoint_path, output_dir)
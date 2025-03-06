import torch
import torch.onnx
from src.models.colony_detector import ColonyDetector
from pathlib import Path
import argparse

def export_to_onnx(checkpoint_path: str, output_path: str, device: str = 'cuda'):
    """
    Export PyTorch model to ONNX format
    
    Args:
        checkpoint_path: Path to PyTorch checkpoint
        output_path: Path to save ONNX model
        device: Device to load model on ('cuda' or 'cpu')
    """
    print(f"Loading checkpoint from {checkpoint_path}")
    
    # Load model
    model = ColonyDetector(pretrained=False)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    print("Model loaded successfully")

    # Create dummy input
    dummy_input = torch.randn(1, 3, 800, 800).to(device)
    
    # Export to ONNX
    print(f"Exporting model to {output_path}")
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        opset_version=11,
        input_names=['input'],
        output_names=['boxes', 'scores', 'labels'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'boxes': {0: 'batch_size'},
            'scores': {0: 'batch_size'},
            'labels': {0: 'batch_size'}
        },
        verbose=True
    )
    
    print("Model exported successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export PyTorch model to ONNX')
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='Path to PyTorch checkpoint')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to save ONNX model')
    parser.add_argument('--device', type=str, default='cuda',
                        help='Device to use (cuda or cpu)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Export model
    export_to_onnx(args.checkpoint, args.output, args.device)

import torch
import tensorrt as trt
from torch2trt import torch2trt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def convert_to_trt(model, dummy_input, output_path="model_trt.engine"):
    """Convert PyTorch model to TensorRT engine"""
    try:
        logger.info("Starting TensorRT conversion...")
        
        # Convert model
        model_trt = torch2trt(
            model,
            [dummy_input],
            fp16_mode=True,
            max_workspace_size=1<<25
        )
        
        # Save engine
        Path(output_path).parent.mkdir(exist_ok=True)
        torch.save(model_trt.state_dict(), output_path)
        logger.info(f"TensorRT engine saved to {output_path}")
        
        return model_trt
    except Exception as e:
        logger.error(f"TRT conversion failed: {str(e)}")
        raise

def load_trt_engine(engine_path):
    """Load a pre-converted TensorRT engine"""
    try:
        logger.info(f"Loading TRT engine from {engine_path}")
        if not Path(engine_path).exists():
            raise FileNotFoundError(f"TRT engine not found at {engine_path}")
            
        # Load engine
        model_trt = torch.load(engine_path)
        logger.info("TRT engine loaded successfully")
        return model_trt
    except Exception as e:
        logger.error(f"Failed to load TRT engine: {str(e)}")
        raise

def create_dummy_input(input_shape=(1, 3, 1280, 1280)):
    """Create dummy input for TRT conversion"""
    return torch.randn(*input_shape).cuda()

if __name__ == "__main__":
    # Example usage
    from model import FasterRCNN  # Import your trained model
    
    # Initialize model
    model = FasterRCNN().cuda().eval()
    
    # Create dummy input
    dummy_input = create_dummy_input()
    
    # Convert and save
    trt_model = convert_to_trt(model, dummy_input)

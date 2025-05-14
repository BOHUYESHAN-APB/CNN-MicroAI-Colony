"""
Test Colony Detection Model (YOLOv6)

This module implements testing functionality for the YOLOv6-based colony detection model.
"""

import cv2
import json
import torch
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime
from scipy import ndimage
from scipy.ndimage import maximum_filter

# Add parent directory to Python path for app imports
sys.path.append(str(Path(__file__).parent.parent.absolute()))
from app_old.analysis_core import ColonyDetector

def safe_mean(values):
    """Calculate mean safely for empty lists."""
    return np.mean(values) if values else 0

def safe_min(values):
    """Get min safely for empty lists."""
    return min(values) if values else 0

def safe_max(values):
    """Get max safely for empty lists."""
    return max(values) if values else 0

def safe_std(values):
    """Calculate standard deviation safely for empty lists."""
    return np.std(values) if values else 0

def load_classes():
    """Load class names from pic-all/classes.txt."""
    classes_file = '../pic-all/classes.txt'
    if not os.path.exists(classes_file):
        print("Warning: classes.txt not found, using default class ['colony']")
        return ['colony']
    with open(classes_file, 'r') as f:
        classes = [line.strip() for line in f]
    return classes

def initialize_dependencies():
    """Initialize all required dependencies."""
    print("Initializing scipy...")
    try:
        import scipy
        print(f"scipy version: {scipy.__version__}")
        from scipy import ndimage
        print("scipy.ndimage imported successfully.")
        return True
    except ImportError:
        print("Error: scipy package is required but not found.")
        print("Please install it using: pip install scipy")
        return False

def main(model_path=None):
    """Test YOLOv6 colony detection model."""
    print("Main function started...")
    print("Testing YOLOv6 colony detection...")
    
    if not initialize_dependencies():
        return

    # Setup paths
    base_dir = Path(__file__).parent.absolute()
    project_root = base_dir.parent

    # Get model path
    print("Determining checkpoint path...")
    if model_path is not None:
        checkpoint_path = Path(model_path)
    else:
        standard_paths = [
            base_dir / 'checkpoints' / 'best_model_20250310_144315.pth',
            base_dir.parent / 'checkpoints' / 'best_model_20250310_144315.pth',
            base_dir / 'best_model_20250310_144315.pth',
            base_dir / 'model.pth'
        ]
        print("Checking standard paths:", standard_paths)

        for path in standard_paths:
            if path.exists():
                checkpoint_path = path
                print(f"Found checkpoint at: {checkpoint_path}")
                break
        else:
            print("\nError: Could not find model checkpoint.")
            print("Tried these locations:")
            for path in standard_paths:
                print(f"  - {path}")
            return

    # Load class names
    classes_path = project_root / 'pic-all' / 'classes.txt'
    if not classes_path.exists():
        print(f"Warning: classes.txt not found at {classes_path}")
        classes = ['colony']
    else:
        with open(classes_path, 'r') as f:
            classes = [line.strip() for line in f]
    print(f"Using classes: {classes}")

    # Initialize model
    try:
        current_dir = Path(__file__).parent.absolute()
        sys.path.append(str(current_dir))  # Add current directory to path for src imports
        from src.models.yolov6 import YOLOv6
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")

        print(f"Loading model from: {checkpoint_path}")
        model = YOLOv6(num_classes=1)
        
        checkpoint = torch.load(checkpoint_path, map_location=device)
        state_dict = checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint
        model.load_state_dict(state_dict, strict=False)
        model.to(device)
        model.eval()
        print("Model initialized and ready.")
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Setup parameters
    params = {
        'confidence': 0.01,
        'min_size': 0,
        'max_size': 999,
        'nms_threshold': 0.28,
        'score_threshold': 0.23,
        'use_gpu': torch.cuda.is_available()
    }

    print("\nDETECTION PARAMETERS")
    print("=" * 50)
    for key, value in params.items():
        print(f"{key}: {value}")

    # Initialize test directory
    test_dir = project_root / 'test-pic'
    if not test_dir.exists():
        print(f"Error: Test directory not found at {test_dir}")
        return

    # Load ground truth data
    try:
        with open(test_dir / "result.json", "r", encoding='utf-8') as f:
            ground_truth = json.load(f)
    except Exception as e:
        print(f"Error loading ground truth data: {e}")
        return

    # Get test images
    test_images = list(test_dir.glob("*.jpg"))
    if not test_images:
        print(f"Error: No test images found in {test_dir}")
        return

    # Setup output directory
    output_dir = base_dir / "test_outputs"
    output_dir.mkdir(exist_ok=True)

    # Initialize processing
    colony_detector = ColonyDetector()
    target_size = 224
    all_results = []

    # Process images
    for img_path in test_images:
        print(f"\nProcessing {img_path.name}...")

        # Get ground truth data
        gt_data = next((item for item in ground_truth if item["图片名称"] == img_path.name), None)
        if gt_data:
            gt_count = gt_data["实际菌落数"]
            merged_count = gt_data["合并菌落数"]
            print(f"Ground truth - Total: {gt_count}, Merged: {merged_count}")
        else:
            gt_count = 0
            merged_count = 0
            print("No ground truth data found")

        # Load and preprocess image
        image = cv2.imread(str(img_path))
        if image is None:
            print(f"Error loading image: {img_path}")
            continue

        # Resize and pad image
        orig_h, orig_w = image.shape[:2]
        scale = min(target_size / orig_w, target_size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        resized = cv2.resize(image, (new_w, new_h))

        square = np.full((target_size, target_size, 3), 0, dtype=np.uint8)
        x_offset = (target_size - new_w) // 2
        y_offset = (target_size - new_h) // 2
        square[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

        # Prepare for model
        preprocessed_image = colony_detector.preprocess_image(square)
        input_tensor = preprocessed_image.unsqueeze(0)
        if device == 'cuda':
            input_tensor = input_tensor.cuda()

        # Run inference
        start_time = datetime.now()
        with torch.no_grad():
            predictions = model(input_tensor)
        processing_time = (datetime.now() - start_time).total_seconds()

        # Process predictions
        score_map = torch.sigmoid(predictions).squeeze().cpu().numpy()
        peaks = score_map > params['score_threshold']
        y_peaks, x_peaks = np.where(peaks)

        # Find colonies
        colonies = []
        scale_factor = orig_w / score_map.shape[1]
        
        for y, x in zip(y_peaks, x_peaks):
            score = score_map[y, x]
            if score < params['confidence']:
                continue

            size = 1
            for r in range(1, 3):
                y1, y2 = max(0, y-r), min(score_map.shape[0], y+r+1)
                x1, x2 = max(0, x-r), min(score_map.shape[1], x+r+1)
                if score_map[y1:y2, x1:x2].mean() < score * 0.7:
                    break
                size = r * 2 + 1

            orig_x = int(x * scale_factor)
            orig_y = int(y * scale_factor)
            orig_radius = int(size * scale_factor / 2)
            
            if params['min_size'] <= orig_radius * 2 <= params['max_size']:
                colonies.append({
                    'x': orig_x,
                    'y': orig_y,
                    'radius': orig_radius,
                    'confidence': float(score)
                })

        # Store results
        results = {
            'filename': img_path.name,
            'ground_truth': gt_count,
            'count': len(colonies),
            'time': processing_time,
            'colonies': colonies,
            'difference': len(colonies) - gt_count,
            'error_rate': (abs(len(colonies) - gt_count) / gt_count * 100) if gt_count > 0 else float('inf') if len(colonies) > 0 else 0
        }
        all_results.append(results)

        print(f"Found {len(colonies)} colonies (Ground truth: {gt_count})")

    print("\nProcessing complete!")
    return all_results

if __name__ == "__main__":
    main()

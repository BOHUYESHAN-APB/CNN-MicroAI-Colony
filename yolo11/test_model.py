"""
Test Colony Detection Model (YOLOv11)
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
from app.analysis_core import ColonyDetector
from .src.utils.config import Config
from .src.utils.dataset import create_dataloader
from .src.utils.transforms import get_test_transforms

def safe_mean(values):
    """Calculate mean safely for empty lists."""
    return np.mean(values) if values else 0

def main(model_path=None):
    """Test YOLOv11 colony detection model."""
    print("Main function started...")
    print("Testing YOLOv11 colony detection...")
    
    if not initialize_dependencies():
        return

    # Setup paths
    base_dir = Path(__file__).parent.absolute()
    project_root = base_dir.parent

    # Load configuration
    config = Config()
    model_config = config.get_model_config()
    testing_config = config.get_testing_config()
    data_config = config.get_data_config()

    # Initialize test directory
    test_dir = project_root / data_config['test']
    if not test_dir.exists():
        print(f"Error: Test directory not found at {test_dir}")
        return

    # Load class names
    classes_path = project_root / data_config['classes']
    if not classes_path.exists():
        print(f"Warning: classes.txt not found at {classes_path}")
        classes = ['colony']
    else:
        with open(classes_path, 'r') as f:
            classes = [line.strip() for line in f]
    print(f"Using classes: {classes}")

    # Initialize model
    try:
        from src.models.yolo11 import YOLO11Detector
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Using device: {device}")

        # Load checkpoint
        print(f"Loading model from: {checkpoint_path}")
        model = YOLO11Detector(num_classes=model_config['num_classes'])
        model.to(device)

        checkpoint = torch.load(checkpoint_path, map_location=device)
        state_dict = checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint
        model.load_state_dict(state_dict, strict=False)
        model.eval()
        print("Model initialized and ready.")

    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Create test dataloader
    test_transforms = get_test_transforms(input_size=model_config['input_size'])
    test_loader = create_dataloader(
        data_root=str(test_dir),
        batch_size=1,
        num_workers=0,
        transforms=test_transforms,
        train=False
    )

    # Initialize ColonyDetector for preprocessing
    colony_detector = ColonyDetector()

    # Process images
    total_detection_count = 0
    total_ground_truth = 0
    all_results = []

    print("\nStarting testing...")
    with torch.no_grad():
        for i, (images, targets, metadata) in enumerate(test_loader):
            # Load test images
            test_dir = project_root / 'test-pic'
            test_images = list(test_dir.glob("*.jpg"))
            if not test_images:
                print(f"Error: No test images found in {test_dir}")
            img_path = test_images[i]
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
                print("Warning: No ground truth data found for this image")
            total_ground_truth += gt_count

            # Load and preprocess image
            image = images.to(device)
            
            # Run inference
            start_time = datetime.now()
            predictions = model(image)
            processing_time = (datetime.now() - start_time).total_seconds()

            # Process predictions
            score_map = torch.sigmoid(predictions).squeeze().cpu().numpy()
            peaks = score_map > testing_config['score_threshold']
            y_peaks, x_peaks = np.where(peaks)

            # Find colonies
            colonies = []
            scale_factor = image.shape[3] / score_map.shape[1]
            
            for y, x in zip(y_peaks, x_peaks):
                score = score_map[y, x]
                if score < testing_config['confidence']:
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
                
                if testing_config['min_size'] <= orig_radius * 2 <= testing_config['max_size']:
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

            total_detection_count += results['count']
            print(f"Found {results['count']} colonies (Ground truth: {gt_count})")
            print(f"Difference: {results['difference']} ({results['error_rate']:.1f}% error)")
            print(f"Processing time: {results['time']:.2f} seconds")

        # Print summary
        print("\n" + "="*50)
        print("OVERALL RESULTS")
        print("="*50)
        print(f"Total detections: {total_detection_count}")
        print(f"Total ground truth: {total_ground_truth}")

        # Calculate average error rate
        valid_errors = [r['error_rate'] for r in all_results if r['error_rate'] != float('inf')]
        if valid_errors:
            avg_error_rate = safe_mean(valid_errors)
            print(f"Average error rate: {avg_error_rate:.1f}%")
        else:
            print("No valid error rates to average")

        print(f"Total processing time: {total_time:.2f} seconds")

        # Print detailed results
        print("\nDetailed Results:")
        print("-" * 40)
        for result in all_results:
            print(f"Filename: {result['filename']}")
            print(f"  Detected colonies: {result['count']}")
            print(f"  Ground Truth: {result['ground_truth']}")
            print(f"  Error Rate: {result['error_rate']:.2f}%")

    return all_results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Path to model checkpoint')
    args = parser.parse_args()
    main(model_path=args.model)

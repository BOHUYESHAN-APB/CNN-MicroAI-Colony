import os
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from torchvision.transforms import functional as F
from models.colony_detector import ColonyDetector
# from data.dataset import ColonyDataset # Assuming ColonyDataset is not strictly needed for direct image evaluation
import argparse # Import argparse
from pathlib import Path # Import Path

def load_model(checkpoint_path, device):
    """Load trained model from checkpoint"""
    model = ColonyDetector(pretrained=False).to(device) # Ensure num_classes matches the trained model if not default
    checkpoint = torch.load(checkpoint_path, map_location=device)
    # Adjust key if necessary, e.g., if checkpoint is from a different saving mechanism
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    elif 'state_dict' in checkpoint: # Common in other frameworks or custom saves
        model.load_state_dict(checkpoint['state_dict'])
    else:
        model.load_state_dict(checkpoint) # Assuming the checkpoint is the state_dict itself
    model.eval()
    return model

def visualize_predictions(image, prediction, score_threshold=0.5, save_path=None):
    """Visualize colony detections on image"""
    image_vis = image.copy() # Use a copy for visualization to avoid modifying the original
    
    # Get predictions above threshold
    boxes = prediction['boxes'].cpu().numpy()
    scores = prediction['scores'].cpu().numpy()
    valid_detections = scores >= score_threshold
    
    boxes = boxes[valid_detections]
    scores = scores[valid_detections]
    
    # Draw bounding boxes and scores
    for box, score in zip(boxes, scores):
        x1, y1, x2, y2 = box # FasterRCNN typically returns x1, y1, x2, y2
        cv2.rectangle(image_vis,
                     (int(x1), int(y1)),
                     (int(x2), int(y2)), # Use x2, y2 for the second point
                     (0, 255, 0), 2)
        cv2.putText(image_vis,
                   f'{score:.2f}',
                   (int(x1), int(y1-5)),
                   cv2.FONT_HERSHEY_SIMPLEX,
                   0.5,
                   (0, 255, 0),
                   2)
    
    # Add colony count
    count = len(boxes)
    cv2.putText(image_vis,
                f'Colony Count: {count}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2)
    
    if save_path:
        cv2.imwrite(save_path, cv2.cvtColor(image_vis, cv2.COLOR_RGB2BGR))
    
    return image_vis

def evaluate_image(model, image_path, device, save_dir=None, score_threshold=0.5):
    """Evaluate single image and visualize results"""
    # Load and preprocess image
    image = cv2.imread(str(image_path)) # Ensure image_path is a string
    if image is None:
        print(f"Error: Could not load image {image_path}")
        return
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) # Convert to RGB
    
    # Convert to tensor
    image_tensor = F.to_tensor(image_rgb).unsqueeze(0).to(device)
    
    # Get predictions
    with torch.no_grad():
        prediction = model.predict(image_tensor)[0] # model.predict should return a list of predictions
    
    # Visualize results
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, Path(image_path).name) # Use Path for basename
    else:
        save_path = None
    
    result_image = visualize_predictions(image_rgb, prediction, save_path=save_path, score_threshold=score_threshold)
    
    # Display results
    plt.figure(figsize=(12, 8))
    plt.imshow(result_image)
    plt.axis('off')
    plt.title(f'Detected Colonies in {Path(image_path).name}: {ColonyDetector.get_colony_count(prediction, score_threshold=score_threshold)}')
    plt.show()

def evaluate_images_in_directory(model, images_dir, device, save_dir='results', score_threshold=0.5):
    """Evaluate all images in a directory"""
    image_paths = list(Path(images_dir).glob('*.jpg')) + \
                  list(Path(images_dir).glob('*.png')) + \
                  list(Path(images_dir).glob('*.jpeg'))
    
    if not image_paths:
        print(f"No images found in {images_dir}")
        return

    os.makedirs(save_dir, exist_ok=True)
    
    total_detected_colonies = 0
    
    for image_path in image_paths:
        print(f"Processing {image_path.name}...")
        # Load and preprocess image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Warning: Could not load image {image_path.name}")
            continue
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tensor = F.to_tensor(image_rgb).unsqueeze(0).to(device)
        
        # Get predictions
        with torch.no_grad():
            prediction = model.predict(image_tensor)[0]
        
        pred_count = ColonyDetector.get_colony_count(prediction, score_threshold=score_threshold)
        total_detected_colonies += pred_count
        
        print(f'  Predicted count: {pred_count}')
        
        # Save visualization
        current_save_path = os.path.join(save_dir, f'result_{image_path.name}')
        visualize_predictions(image_rgb, prediction, save_path=current_save_path, score_threshold=score_threshold)
        print(f"  Saved visualization to {current_save_path}")

    print(f'\nTotal detected colonies in {images_dir}: {total_detected_colonies}')


def main():
    parser = argparse.ArgumentParser(description="Evaluate Colony Detection Model")
    parser.add_argument('--checkpoint', type=str, required=True, help='Path to the model checkpoint file.')
    parser.add_argument('--images_dir', type=str, default='test-pic', help='Directory containing test images.')
    parser.add_argument('--save_dir', type=str, default='test_outputs/evaluate_results', help='Directory to save result images.')
    parser.add_argument('--score_threshold', type=float, default=0.5, help='Score threshold for detections.')
    parser.add_argument('--use_gpu', action='store_true', help='Use GPU if available (Intel iGPU will use CPU via OpenVINO/ONNX if supported, otherwise PyTorch CPU).')
    
    args = parser.parse_args()

    # For Intel iGPU, PyTorch typically falls back to CPU unless specific OpenVINO/ONNX runtime integration is used.
    # We will prioritize CPU for broader compatibility as requested.
    if args.use_gpu and torch.cuda.is_available():
        DEVICE = torch.device('cuda')
    else:
        DEVICE = torch.device('cpu')
    print(f"Using device: {DEVICE}")

    CHECKPOINT_PATH = args.checkpoint
    IMAGES_DIR = args.images_dir
    SAVE_DIR = args.save_dir
    SCORE_THRESHOLD = args.score_threshold

    if not Path(CHECKPOINT_PATH).exists():
        print(f"Error: Checkpoint file not found at {CHECKPOINT_PATH}")
        return

    if not Path(IMAGES_DIR).is_dir():
        print(f"Error: Images directory not found at {IMAGES_DIR}")
        return
        
    # Load model
    print(f"Loading model from {CHECKPOINT_PATH}...")
    model = load_model(CHECKPOINT_PATH, DEVICE)
    print("Model loaded successfully.")
    
    # Evaluate all images in the directory
    print(f"Evaluating images in {IMAGES_DIR}...")
    evaluate_images_in_directory(model, IMAGES_DIR, DEVICE, SAVE_DIR, SCORE_THRESHOLD)
    print(f"Evaluation complete. Results saved in {SAVE_DIR}")

if __name__ == '__main__':
    main()

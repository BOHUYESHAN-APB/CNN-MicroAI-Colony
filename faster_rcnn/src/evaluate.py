import os
import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt
from torchvision.transforms import functional as F
from models.colony_detector import ColonyDetector
from data.dataset import ColonyDataset

def load_model(checkpoint_path, device):
    """Load trained model from checkpoint"""
    model = ColonyDetector(pretrained=False).to(device)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    return model

def visualize_predictions(image, prediction, score_threshold=0.5, save_path=None):
    """Visualize colony detections on image"""
    image = image.copy()
    
    # Get predictions above threshold
    boxes = prediction['boxes'].cpu().numpy()
    scores = prediction['scores'].cpu().numpy()
    valid_detections = scores >= score_threshold
    
    boxes = boxes[valid_detections]
    scores = scores[valid_detections]
    
    # Draw bounding boxes and scores
    for box, score in zip(boxes, scores):
        x1, y1, w, h = box
        cv2.rectangle(image, 
                     (int(x1), int(y1)), 
                     (int(x1+w), int(y1+h)),
                     (0, 255, 0), 2)
        cv2.putText(image, 
                   f'{score:.2f}',
                   (int(x1), int(y1-5)),
                   cv2.FONT_HERSHEY_SIMPLEX,
                   0.5,
                   (0, 255, 0),
                   2)
    
    # Add colony count
    count = len(boxes)
    cv2.putText(image,
                f'Colony Count: {count}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2)
    
    if save_path:
        cv2.imwrite(save_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    
    return image

def evaluate_image(model, image_path, device, save_dir=None):
    """Evaluate single image and visualize results"""
    # Load and preprocess image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert to tensor
    image_tensor = F.to_tensor(image).unsqueeze(0).to(device)
    
    # Get predictions
    with torch.no_grad():
        prediction = model.predict(image_tensor)[0]
    
    # Visualize results
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, os.path.basename(image_path))
    else:
        save_path = None
    
    result_image = visualize_predictions(image, prediction, save_path=save_path)
    
    # Display results
    plt.figure(figsize=(12, 8))
    plt.imshow(result_image)
    plt.axis('off')
    plt.title(f'Detected Colonies: {model.get_colony_count(prediction)}')
    plt.show()

def evaluate_dataset(model, dataset_dir, device, save_dir='results'):
    """Evaluate all images in dataset"""
    dataset = ColonyDataset(dataset_dir, split='test')
    
    total_error = 0
    total_images = len(dataset)
    
    os.makedirs(save_dir, exist_ok=True)
    
    for idx in range(total_images):
        sample = dataset[idx]
        image_path = sample['img_path']
        true_count = sample['total_count']
        
        # Load and preprocess image
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tensor = F.to_tensor(image).unsqueeze(0).to(device)
        
        # Get predictions
        with torch.no_grad():
            prediction = model.predict(image_tensor)[0]
        
        pred_count = model.get_colony_count(prediction)
        error = abs(pred_count - true_count)
        total_error += error
        
        # Save visualization
        save_path = os.path.join(save_dir, f'result_{idx}.jpg')
        visualize_predictions(image, prediction, save_path=save_path)
        
        print(f'Image {idx+1}/{total_images}:')
        print(f'  Predicted count: {pred_count}')
        print(f'  True count: {true_count}')
        print(f'  Error: {error}\n')
    
    mean_error = total_error / total_images
    print(f'\nMean counting error: {mean_error:.2f}')

def main():
    # Settings
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    CHECKPOINT_PATH = 'path/to/best/checkpoint.pth'  # Update with actual path
    TEST_IMAGE_PATH = 'path/to/test/image.jpg'      # Update with actual path
    
    # Load model
    model = load_model(CHECKPOINT_PATH, DEVICE)
    
    # Evaluate single image
    evaluate_image(model, TEST_IMAGE_PATH, DEVICE)
    
    # Evaluate entire dataset
    evaluate_dataset(model, 'pic', DEVICE)

if __name__ == '__main__':
    main()

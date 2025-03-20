import os
import glob
import random
import json
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torchvision import transforms
from models.yolov6 import YOLOv6

# Configuration
IMAGE_DIR = 'pic-all'
BATCH_SIZE = 16
LEARNING_RATE = 0.001
NUM_EPOCHS = 10
CHECKPOINT_DIR = 'yolo6/checkpoints'
SAVE_FREQ = 1  # Save checkpoint every N epochs

# 1. Data Preparation
def load_data(image_dir):
    image_files = glob.glob(os.path.join(image_dir, '**/*.jpg'), recursive=True) + \
                  glob.glob(os.path.join(image_dir, '**/*.png'), recursive=True)
    print(f"Found {len(image_files)} image files in {image_dir}")
    return image_files

import json
from PIL import Image

def load_annotations(image_path):
    annotation_path = image_path.replace('.jpg', '.json').replace('.png', '.json')  # YOLO format: .json
    print(f"Loading annotations from: {annotation_path}")  # Print annotation path
    if not os.path.exists(annotation_path):
        print(f"Annotation file not found: {annotation_path}")
        return []

    try:
        with open(annotation_path, 'r') as f:
            data = json.load(f)
            print(f"JSON data: {data}")  # Print JSON data
            annotations = []
            # Get image dimensions
            try:
                image = Image.open(image_path)
                image_width, image_height = image.size
            except FileNotFoundError:
                print(f"Image file not found: {image_path}")
                return []

            # Assuming the JSON file contains a list of objects, each with bounding box information
            for obj in data['labels']:
                # Extract bounding box coordinates and class ID from the JSON object
                # The bounding box coordinates are in the format (x, y, width, height)
                class_name = obj.get('class', 'S.aureus')  # Default to 'S.aureus' if 'class' is missing
                x = obj.get('x', 0)
                y = obj.get('y', 0)
                width = obj.get('width', 0)
                height = obj.get('height', 0)

                # Normalize the bounding box coordinates
                x_center = (x + width / 2) / image_width
                y_center = (y + height / 2) / image_height
                width_normalized = width / image_width
                height_normalized = height / image_height

                # Get class ID from class name
                # Assuming classes are loaded from classes.txt
                try:
                    class_id = classes.index(class_name)
                except ValueError:
                    print(f"Warning: Class '{class_name}' not found in classes.txt. Using default class 0.")
                    class_id = 0

                annotations.append([class_id, x_center, y_center, width_normalized, height_normalized])
            return annotations
    except FileNotFoundError:
        print(f"Annotation file not found: {annotation_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {annotation_path}")
        return []

def load_classes(image_dir):
    classes_file = os.path.join('pic-all', 'classes.txt')
    if not os.path.exists(classes_file):
        return ['colony']  # Default class if classes.txt is missing

    with open(classes_file, 'r') as f:
        classes = [line.strip() for line in f]
    return classes

# 2. Model Definition (YOLOv6 is already defined)

# 3. Training Loop
def train(model, image_files, classes, optimizer, criterion, num_epochs, checkpoint_dir):
    os.makedirs(checkpoint_dir, exist_ok=True)
    best_loss = float('inf')
    start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    for epoch in range(num_epochs):
        random.shuffle(image_files)  # Shuffle data each epoch
        for image_file in image_files:
            annotations = load_annotations(image_file)
            if not annotations:
                print(f"Skipping image {image_file} due to missing or invalid annotations.")
                continue

            try:
                image = Image.open(image_file).convert('RGB')
                image = transform(image)
            except FileNotFoundError:
                print(f"Skipping image {image_file} because the image file was not found.")
                continue

            # Use class IDs from annotations as target
            num_labels = len(annotations)
            if num_labels == 0:
                print(f"Skipping image {image_file} because it has no labels.")
                continue

            # For simplicity, use the class ID of the first annotation as target
            # In real object detection, you would use bounding boxes and class IDs for loss calculation
            target_class_id = annotations[0][0] # Get class ID of the first annotation
            # Placeholder target with correct shape for debugging - replace with proper YOLO target later
            output = model(image.unsqueeze(0))  # Add batch dimension
            target = torch.randn_like(output)

            # Forward pass

            print(f"Output shape: {output.shape}")
            print(f"Target shape: {target.shape}")
            # --- YOLOv6 Loss Implementation ---
            # TODO: Implement proper YOLOv6 loss function here
            # This is a placeholder for the actual YOLOv6 loss calculation.
            # YOLOv6 loss typically includes:
            #   - Classification loss (for class probabilities)
            #   - Regression loss (for bounding box coordinates - e.g., CIoU loss)
            #   - Objectness loss (to determine if an object is present in a grid cell)

            # Placeholder for combined YOLOv6 loss
            # Replace this with the actual YOLOv6 loss calculation
            loss = torch.tensor([0.0], requires_grad=True) # Example: Placeholder loss set to 0.0

            # For demonstration purposes, let's assume a simple classification loss for now
            # (This is still a simplification and needs to be replaced with the full YOLOv6 loss)
            # If your YOLOv6 model outputs class probabilities, you might use CrossEntropyLoss for classification
            # loss_classification = nn.CrossEntropyLoss()(output_classification, target_classification)
            # loss += loss_classification # Add classification loss to the total loss

            # Similarly, you would add regression and objectness losses here
            # loss_regression = ... # Calculate regression loss (e.g., CIoU loss)
            # loss += loss_regression # Add regression loss

            # loss_objectness = ... # Calculate objectness loss
            # loss += loss_objectness # Add objectness loss

            # --- End of YOLOv6 Loss Implementation ---

            # --- Placeholder Loss (Replace with actual YOLOv6 loss) ---
            # For demonstration, using MSE loss between output and a random target
            loss = criterion(output, target) # Example: MSE Loss
            # --- End Placeholder Loss ---

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            print(f'Epoch [{epoch+1}/{num_epochs}], Image: {image_file}, Loss: {loss.item():.4f}')
        
        # Save checkpoint at specified frequency
        if (epoch + 1) % SAVE_FREQ == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f'checkpoint_epoch_{epoch+1}_{start_time}.pth')
            model.save(checkpoint_path)
            print(f'Saved checkpoint to {checkpoint_path}')
            
            # Save training state
            training_state = {
                'epoch': epoch,
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': loss.item(),
                'classes': classes
            }
            state_path = os.path.join(checkpoint_dir, f'training_state_{start_time}.pth')
            torch.save(training_state, state_path)
            
            # Save best model
            if loss.item() < best_loss:
                best_loss = loss.item()
                best_model_path = os.path.join(checkpoint_dir, f'best_model_{start_time}.pth')
                model.save(best_model_path)
                print(f'New best model saved with loss: {best_loss:.4f}')

if __name__ == '__main__':
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    # Load data and classes
    image_files = load_data(IMAGE_DIR)
    classes = load_classes(IMAGE_DIR)
    num_classes = len(classes)

    # Model, optimizer, and loss function
    model = YOLOv6(num_classes)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()  # Example loss function

    # Train the model
    train(model, image_files, classes, optimizer, criterion, NUM_EPOCHS, CHECKPOINT_DIR)

    print('Finished Training')

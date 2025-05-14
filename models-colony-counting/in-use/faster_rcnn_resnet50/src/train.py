import os
import sys
import torch
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
import logging
import json
from datetime import datetime

# Add the project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.data.dataset import ColonyDataset
from src.models.colony_detector import ColonyDetector

def setup_logging(save_dir):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(save_dir, 'training.log')),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def save_checkpoint(model, optimizer, epoch, save_dir, metrics=None):
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'metrics': metrics
    }
    path = os.path.join(save_dir, f'checkpoint_epoch_{epoch}.pth')
    torch.save(checkpoint, path)

def train_one_epoch(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0
    progress_bar = tqdm(dataloader, desc='Training')
    
    for batch_idx, batch in enumerate(progress_bar):
        print(f"\nProcessing batch {batch_idx+1}")
        try:
            # Each item in batch is a dictionary
            images = [item['image'].to(device) for item in batch]
            targets = []
            for item in batch:
                target = {
                    'boxes': item['boxes'].to(device),
                    'labels': item['labels'].to(device)
                }
                targets.append(target)
            
            print(f"Batch loaded to {device}")
            
            optimizer.zero_grad()
            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())
            print(f"Forward pass completed, loss: {losses.item()}")
            
            losses.backward()
            print("Backward pass completed")
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            total_loss += losses.item()
            progress_bar.set_postfix({'loss': losses.item()})
            
            print(f"Memory allocated: {torch.cuda.memory_allocated(device)/1e9:.2f}GB")
            print(f"Memory cached: {torch.cuda.memory_reserved(device)/1e9:.2f}GB")
            
        except Exception as e:
            print(f"Error in batch {batch_idx}: {str(e)}")
            raise e
    
    return total_loss / len(dataloader)

def validate(model, dataloader, device):
    model.eval()
    total_error = 0
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc='Validation'):
            # Each item in batch is a dictionary
            images = [item['image'].to(device) for item in batch]
            true_counts = [item['total_count'] for item in batch]
            
            predictions = model.predict(images)
            pred_counts = [model.get_colony_count(pred) for pred in predictions]
            
            # Calculate counting error
            errors = [abs(pred - true) for pred, true in zip(pred_counts, true_counts)]
            total_error += sum(errors)
    
    return total_error / len(dataloader.dataset)

def main():
    # Check GPU availability and configure device
    if not torch.cuda.is_available():
        print("WARNING: CUDA is not available! Falling back to CPU...")
        DEVICE = torch.device('cpu')
    else:
        DEVICE = torch.device('cuda:0')
        torch.cuda.empty_cache()  # Clear GPU memory
        print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        print(f"Initial GPU memory: {torch.cuda.memory_allocated()/1e9:.2f}GB")
    
    # Training settings
    BATCH_SIZE = 4
    EPOCHS = 50
    LEARNING_RATE = 0.001
    
    # Create save directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_dir = os.path.join('checkpoints', f'run_{timestamp}')
    os.makedirs(save_dir, exist_ok=True)
    
    # Setup logging
    logger = setup_logging(save_dir)
    logger.info(f'Training on device: {DEVICE}')
    
    # Load dataset
    dataset = ColonyDataset('pic')
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=lambda x: x, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=lambda x: x, pin_memory=True)
    
    logger.info(f'Train dataset size: {len(train_dataset)}')
    logger.info(f'Validation dataset size: {len(val_dataset)}')
    
    try:
        # Initialize model
        print("Initializing model...")
        model = ColonyDetector(pretrained=True).to(DEVICE)
        optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
        print("Model initialized successfully")
        
        # Training loop
        best_val_error = float('inf')
        metrics_history = []
        
        for epoch in range(EPOCHS):
            logger.info(f'Epoch {epoch+1}/{EPOCHS}')
            
            # Train
            train_loss = train_one_epoch(model, train_loader, optimizer, DEVICE)
            logger.info(f'Training loss: {train_loss:.4f}')
            
            # Validate
            val_error = validate(model, val_loader, DEVICE)
            logger.info(f'Validation mean count error: {val_error:.4f}')
            
            # Save metrics
            metrics = {
                'epoch': epoch + 1,
                'train_loss': train_loss,
                'val_error': val_error
            }
            metrics_history.append(metrics)
            
            # Save best model
            if val_error < best_val_error:
                best_val_error = val_error
                save_checkpoint(model, optimizer, epoch + 1, save_dir, metrics)
                logger.info('Saved new best model')
            
            # Save metrics history
            with open(os.path.join(save_dir, 'metrics_history.json'), 'w') as f:
                json.dump(metrics_history, f, indent=4)
                
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        save_checkpoint(model, optimizer, epoch + 1, save_dir, metrics)
        logger.info("Saved checkpoint before exiting")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        raise e

if __name__ == '__main__':
    main()

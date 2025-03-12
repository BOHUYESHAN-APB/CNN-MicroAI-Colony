"""
Training script for YOLOv11 colony detector.
"""

print("TRAIN.PY SCRIPT IS RUNNING") # Added print statement

import os
os.environ["ALBUMENTATIONS_DISABLE_CHECKING"] = "1"  # 禁用版本检查

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
import logging
import yaml # Import YAML
from datetime import datetime

from models.yolo11 import YOLO11Detector
from utils.dataset import create_dataloader # Import dataloader utility
from utils.transforms import get_train_transforms, get_val_transforms # Import transform utils
from utils.config import Config # Import config utility

def setup_logger():
    """Set up logging configuration."""
    log_dir = '../logs'  # Log directory path relative to yolo11
    os.makedirs(log_dir, exist_ok=True)  # Ensure log directory exists

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(os.path.join(log_dir, f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'))  # Log path relative to yolo11

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


class Trainer:
    def __init__(self, config_path='C:/Users/ETPau/Documents/GitHub/CNN-MicroAI-Colony/yolo11/config.yaml'):  # Hardcoded absolute config path as default
        print(f"Script directory: {os.path.dirname(__file__)}") # Print script directory
        print(f"Config path (before Config init): {config_path}") # Print config path INSIDE init
        self.config = Config(config_path)  # Load config
        self.logger = setup_logger()
        self.device = torch.device(self.config['training']['device'] if torch.cuda.is_available() else 'cpu')

        # Initialize model
        self.model = YOLO11Detector(num_classes=self.config['model']['num_classes']).to(self.device)

        # Setup optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config['training']['learning_rate'],
            weight_decay=self.config['training']['weight_decay']
        )

        # Setup data loaders (initialize before scheduler)
        self.train_loader, self.val_loader = self._create_dataloaders()

        # Learning rate scheduler - initialized AFTER dataloaders
        self.scheduler = optim.lr_scheduler.OneCycleLR(
            self.optimizer,
            max_lr=self.config['training']['learning_rate'],
            epochs=self.config['training']['epochs'],
            steps_per_epoch=len(self.train_loader),
            pct_start=0.1
        )

        # Setup checkpoint directory
        checkpoint_dir = '../checkpoints'  # Checkpoint dir relative to yolo11
        os.makedirs(checkpoint_dir, exist_ok=True)

    def _create_dataloaders(self):
        """Create training and validation dataloaders."""
        train_data_root = self.config['data']['train_path'] # Use train_path from config
        val_data_root = self.config['data']['val_path']     # Use val_path from config

        train_loader = create_dataloader(
            data_root=train_data_root, # Use train_data_root
            batch_size=self.config['training']['batch_size'],
            num_workers=self.config['training']['num_workers'],
            transforms=get_train_transforms(config=self.config, input_size=self.config['model']['image_size']),
            train=True,
            config=self.config['data']
        )

        val_loader = create_dataloader(
            data_root=val_data_root,   # Use val_data_root
            batch_size=self.config['training']['batch_size'],
            num_workers=self.config['training']['num_workers'],
            transforms=get_val_transforms(input_size=self.config['model']['image_size']),
            train=False,
            config=self.config['data']
        )

        print(f"Length of train_loader: {len(train_loader)}") # Print train_loader length
        return train_loader, val_loader

    def train_epoch(self):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0

        for batch_idx, (images, targets, _) in enumerate(self.train_loader): # Unpack metadata
            images = images.to(self.device)
            targets = targets.to(self.device)

            self.optimizer.zero_grad()

            predictions = self.model(images)
            loss, loss_components = self.model.get_loss(predictions, targets)

            # Mixed precision scaling
            if self.config['training']['amp']:
                scaler = torch.cuda.amp.GradScaler()
                with torch.cuda.amp.autocast():
                    predictions = self.model(images)
                    loss, loss_components = self.model.get_loss(predictions, targets)
                scaler.scale(loss).backward()
                scaler.step(self.optimizer)
                scaler.update()
            else:
                predictions = self.model(images)
                loss, loss_components = self.model.get_loss(predictions, targets)
                loss.backward()
                self.optimizer.step()

            self.scheduler.step()
            total_loss += loss.item()

            if batch_idx % self.config['training']['log_interval'] == 0:
                log_message_parts = [
                    f"Train Batch {batch_idx}/{len(self.train_loader)} ",
                    f"Loss: {loss.item():.4f}"
                ]
                if loss_components:  # Check if loss_components is not None
                    log_message_parts.extend([
                        f"(Objectness: {loss_components['obj_loss']:.4f}, ",
                        f"Class: {loss_components['cls_loss']:.4f}, ",
                        f"Regression: {loss_components['reg_loss']:.4f})"
                    ])
                self.logger.info("".join(log_message_parts))

        return total_loss / len(self.train_loader)

    def validate(self):
        """Validate the model on validation set."""
        self.model.eval()
        total_loss = 0

        with torch.no_grad():
            for images, targets, _ in self.val_loader: # Unpack metadata
                images = images.to(self.device)
                targets = targets.to(self.device)

                predictions = self.model(images)
                loss, _ = self.model.get_loss(predictions, targets)
                total_loss += loss.item()

        return total_loss / len(self.val_loader)

    def save_checkpoint(self, epoch, val_loss, is_best=False):
        """Save model checkpoint."""
        checkpoint_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "checkpoints")) # Absolute checkpoint dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        checkpoint_file = f"checkpoint_epoch_{epoch+1:03d}.pth"
        checkpoint_path = os.path.join(checkpoint_dir, checkpoint_file) # Correct path

        torch.save({ # Save checkpoint dictionary
            'epoch': epoch + 1,
            'state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': val_loss,
        }, checkpoint_path)
        self.logger.info(f"Checkpoint saved to {checkpoint_path}") # Log save
        print(f"Absolute checkpoint path: {os.path.abspath(checkpoint_path)}") # Print absolute path

if __name__ == '__main__':
    try:
        config_path = 'config.yaml' # Path to your configuration file - now potentially overridden by default in Trainer init
        print(f"Config path (before Trainer init): {config_path}") # Print path BEFORE Trainer init
        print(f"Loading config from {os.path.abspath(config_path)}")
        trainer = Trainer() # Instantiate Trainer WITHOUT passing config_path, relying on default

        print("Starting training...")
        for epoch in range(trainer.config['training']['epochs']):
            try:
                print(f"Starting epoch {epoch+1}")
                train_loss = trainer.train_epoch()
                print(f"Training loss: {train_loss:.4f}")
                val_loss = trainer.validate()
                print(f"Validation loss: {val_loss:.4f}")
                trainer.save_checkpoint(epoch, val_loss)
                print(f"Epoch {epoch+1}/{trainer.config['training']['epochs']}, Training Loss: {train_loss:.4f}, Validation Loss: {val_loss:.4f}")
            except Exception as e:
                print(f"Error during epoch {epoch+1}: {str(e)}")
                raise
        print("Training finished.")
    except Exception as e:
        print(f"Training failed with error: {str(e)}")
        raise

import os
import sys
import torch
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("="*80)
        logger.info("SYSTEM INFORMATION")
        logger.info("="*80)
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Absolute current directory: {os.path.abspath('.')}")
        logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")
        
        logger.info("\nFull directory listing:")
        for root, dirs, files in os.walk('.'):
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 4 * level
            logger.info(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                logger.info(f"{subindent}{f}")

        logger.info("\n" + "="*80)
        logger.info("CONFIG LOADING")
        logger.info("="*80)
        
        current_dir = os.path.abspath('.')
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            logger.info(f"Added {current_dir} to Python path")
        
        logger.info("\nTrying to import utils.config...")
        from utils.config import Config
        logger.info("Successfully imported Config")
        
        config_path = os.path.abspath('config.yaml')
        logger.info(f"\nChecking if config file exists at {config_path}...")
        if os.path.exists(config_path):
            logger.info("Config file found")
            
            logger.info("\nTrying to load config through Config class...")
            config = Config(config_path)
            logger.info("Config loaded successfully")
            
            logger.info("\nTrying to access config values...")
            logger.info(f"model.num_classes: {config['model']['num_classes']}")
            logger.info(f"model.image_size: {config['model']['image_size']}")
            logger.info(f"data.train_path: {config['data']['train_path']}")
            logger.info(f"training.device: {config['training']['device']}")
            
        else:
            logger.warning("Config file not found!")
            logger.info("Looking for config.yaml in parent directories...")
            parent = os.path.dirname(current_dir)
            while parent and parent != os.path.dirname(parent):
                test_path = os.path.join(parent, 'config.yaml')
                if os.path.exists(test_path):
                    logger.info(f"Found config file at: {test_path}")
                    break
                parent = os.path.dirname(parent)
            
        logger.info("\n" + "="*80)
        logger.info("DATALOADER CREATION")
        logger.info("="*80)
        
        # Create trainer
        logger.info("Creating trainer...")
        trainer = Trainer(config_path)
        logger.info("Trainer created successfully")
        
        # Data loaders
        logger.info("\nCreating dataloaders...")
        train_loader, val_loader = trainer._create_dataloaders()
        logger.info("Dataloaders created successfully")

        logger.info("\nChecking train dataloader...")
        logger.info(f"Train dataloader: {train_loader}")
        logger.info(f"Number of training batches: {len(train_loader)}")

        logger.info("\nChecking validation dataloader...")
        logger.info(f"Validation dataloader: {val_loader}")
        logger.info(f"Number of validation batches: {len(val_loader)}")
        
        # Train for one epoch
        logger.info("Starting training...");
        epochs = 1
        for epoch in range(epochs):
            logger.info(f"Starting epoch {epoch+1}/{epochs}")
            train_loss = trainer.train_epoch()
            logger.info(f"Epoch {epoch+1}/{epochs} completed, training loss: {train_loss:.4f}")
            
            val_loss = trainer.validate()
            logger.info(f"Validation loss: {val_loss:.4f}")
            
            trainer.save_checkpoint(epoch, val_loss)
            logger.info("Checkpoint saved")
            
        logger.info("Training completed successfully")
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        raise

class Trainer:
    def __init__(self, config_path):  # Accept config path
        self.config = Config(config_path)  # Load config
        self.logger = logging.getLogger(__name__) # Use logger from main script
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
        logger = logging.getLogger(__name__) # Get logger
        logger.info("Starting _create_dataloaders") # Add log

        train_config = self.config['data']['train_path']
        val_config = self.config['data']['val_path']
        logger.info(f"Train data path from config: {train_config}") # Log train config path
        logger.info(f"Val data path from config: {val_config}") # Log val config path
        
        train_loader = create_dataloader(
            data_root=train_config,
            batch_size=self.config['training']['batch_size'],
            num_workers=self.config['training']['num_workers'],
            transforms=get_train_transforms(config=self.config, input_size=self.config['model']['image_size']),
            train=True,
            config=self.config['data']
        )
        logger.info("Train dataloader created") # Log after train dataloader created
        
        val_loader = create_dataloader(
            data_root=val_config,
            batch_size=self.config['training']['batch_size'],
            num_workers=self.config['training']['num_workers'],
            transforms=get_val_transforms(input_size=self.config['model']['image_size']),
            train=False,
            config=self.config['data']
        )
        logger.info("Validation dataloader created") # Log after val dataloader created
        
        logger.info("Exiting _create_dataloaders") # Log before return
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
                self.logger.info(
                    f"Train Batch {batch_idx}/{len(self.train_loader)} "
                    f"Loss: {loss.item():.4f} "
                    f"(Objectness: {loss_components['obj_loss']:.4f}, " # More descriptive logging
                    f"Class: {loss_components['cls_loss']:.4f}, "
                    f"Regression: {loss_components['reg_loss']:.4f})"
                )
        
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
        config_path = 'config.yaml'  # Path to your configuration file
        print(f"Loading config from {os.path.abspath(config_path)}")
        trainer = Trainer(config_path) # Pass config path to Trainer
        
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

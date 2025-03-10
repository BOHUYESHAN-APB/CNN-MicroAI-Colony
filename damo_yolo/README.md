# DAMO-YOLO Colony Detector

DAMO-YOLO implementation for bacterial colony detection.

## Features

- Optimized backbone network
- Feature Pyramid Network (FPN) for multi-scale detection
- Advanced detection head
- Checkpoint management for training
- CPU and CUDA support

## Directory Structure

```
damo_yolo/
├── checkpoints/          # Model weights storage
├── src/
│   ├── train.py         # Training script
│   └── models/          # Model implementations
└── test_model.py        # Testing script
```

## Usage

### Training

```bash
python src/train.py --data pic-all --epochs 50 --batch-size 16 --lr 0.001
```

Options:
- `--data`: Path to training data (default: pic-all)
- `--epochs`: Number of training epochs (default: 50)
- `--batch-size`: Training batch size (default: 16)
- `--lr`: Learning rate (default: 0.001)
- `--checkpoint-dir`: Directory to save checkpoints
- `--resume`: Resume from checkpoint
- `--device`: Training device (cuda/cpu)

### Testing

```bash
python test_model.py [--model path/to/model.pth]
```

## Model Architecture

1. **Backbone**:
   - Multiple convolutional stages
   - Batch normalization
   - SiLU activation

2. **Neck**:
   - Feature Pyramid Network (FPN)
   - Multi-scale feature fusion

3. **Detection Head**:
   - Convolutional layers
   - Classification branch

## Checkpoints

Checkpoints are saved in `checkpoints/` directory:
- `checkpoint_epoch_XX.pth`: Regular checkpoints
- `best_damo_model.pth`: Best performing model
- `latest_model.pth`: Latest model state

## Requirements

- PyTorch >= 1.7.0
- OpenCV
- NumPy
- SciPy

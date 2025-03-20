# YOLOv11 Colony Detector

YOLOv11 implementation for bacterial colony detection with advanced features.

## Features

- Enhanced backbone with residual connections
- Advanced Feature Pyramid Network (FPN)
- Attention mechanism in detection head
- Multi-scale feature fusion
- State-of-the-art training techniques

## Directory Structure

```
yolo11/
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

1. **Advanced Backbone**:
   - Residual connections
   - Multi-stage feature extraction
   - Deep feature hierarchy
   - BatchNorm with SiLU activation

2. **Enhanced Neck**:
   - Advanced Feature Pyramid Network
   - Lateral connections
   - Feature fusion
   - Upsampling with bilinear interpolation

3. **Attention-based Head**:
   - Channel attention mechanism
   - Multi-scale feature fusion
   - Adaptive feature refinement
   - Final detection layer

## Innovations

1. **Residual Learning**:
   - Improved gradient flow
   - Better feature extraction
   - Enhanced training stability

2. **Attention Mechanism**:
   - Channel-wise attention
   - Adaptive feature weighting
   - Improved detection accuracy

3. **Feature Fusion**:
   - Multi-scale feature integration
   - Enhanced small object detection
   - Better scale handling

## Checkpoints

Checkpoints are saved in `checkpoints/` directory:
- `checkpoint_epoch_XX.pth`: Regular checkpoints
- `best_yolo11_model.pth`: Best performing model
- `latest_model.pth`: Latest model state

## Requirements

- PyTorch >= 1.7.0
- OpenCV
- NumPy
- SciPy

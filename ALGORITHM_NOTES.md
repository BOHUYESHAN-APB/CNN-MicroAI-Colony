# Algorithm Design Notes

## Comparison of Detection Methods

### 1. Analysis of Different Architectures

#### YOLOv7
##### Key Features:
- Single-stage detector
- End-to-end training
- Direct prediction of bounding boxes and class probabilities
- Optimized for real-time detection (100+ FPS on GPU)

##### Advantages:
- High speed for real-time applications
- Good balance between accuracy and speed (approx. 10% AP improvement over YOLOv5)
- Flexible training and dynamic resolution adjustment

##### Limitations:
- Lower accuracy for microscopic object detection
- High memory consumption (model size around 70MB)

#### OpenCV (Traditional Methods)
##### Key Features:
- Non-deep learning methods (Haar cascades, HOG+SVM, template matching)
- Lightweight computation
- CPU-based processing

##### Advantages:
- Low resource requirements (no GPU needed)
- Simple API, suitable for rapid prototyping
- Can directly use pre-trained models

##### Limitations:
- Limited accuracy in complex scenarios
- Single functionality
- Poor scalability

#### Faster R-CNN based on ResNet50
##### Key Features:
- Two-stage detector
- ResNet50 backbone for feature extraction
- Region Proposal Network (RPN)
- Designed for high accuracy

##### Advantages:
- Excellent accuracy, especially for small object detection
- Strong feature extraction capability
- Good interpretability

##### Limitations:
- High computational cost (approx. 200ms per image)
- Large memory footprint (approx. 200MB)
- Requires GPU for efficient processing

## System Integration Strategy

### 1. Implementation Goals
- Combine the advantages of multiple methods
- Balance performance and resource consumption
- Achieve flexible deployment options

### 2. Architecture Design
```plaintext
+-------------------+     +-------------------+     +-------------------+
|  ResNet50         |     | Faster R-CNN      |     | OpenCV            |
| (Base Feature     | →   | (Object Detection)| →   | (Post-processing  |
|  Extraction)      |     | Region Proposal   |     |  Optimization)    |
| Deep Residual     |     | Network           |     | Traditional Image |
| Learning          |     |                   |     | Processing        |
+-------------------+     +-------------------+     +-------------------+
```

### 3. Technical Implementation
1. **Data Preprocessing Pipeline**
   ```python
   def preprocess_pipeline(image):
       # UV spectrum enhancement
       uv_enhanced = enhance_uv_spectrum(image)
       
       # Multispectral fusion
       fused = spectral_fusion(image, uv_enhanced)
       
       # Image normalization
       normalized = normalize_image(fused)
       
       return normalized
   ```

2. **Optimization Strategies**
   - Model compression: quantization, pruning
   - Feature fusion: multi-scale feature pyramid
   - Attention mechanism: CBAM module integration

### 4. Deployment and Optimization
1. **Deployment Options**
   - ONNX format export
   - TensorRT acceleration
   - OpenVINO support

2. **Performance Optimization**
   - Batch processing parallelization
   - GPU memory optimization
   - CPU task allocation

## Integration of Patented Technologies

### 1. Core Technical Components
#### Multispectral Image Fusion
- Supports ultraviolet/infrared imaging
- Enhances colony edge detection
- Multimodal fusion at the feature level

#### Dynamic Feature Selection
- Introduces CBAM attention mechanism
- Optimizes feature extraction process
- Enhances discrimination against complex backgrounds

#### Small Sample Optimization Strategy
- Transfer learning application
- Online Hard Example Mining (OHEM)
- Enhances model generalization ability

## New Version Notes
The new version (app/) uses PySide6 and the PyOneDark theme, providing a more modern user interface and improved performance.

## References and Acknowledgements

### Core Algorithm References

#### ResNet
**Paper**: "Deep Residual Learning for Image Recognition"
```bibtex
@article{he2015deep,
  title={Deep Residual Learning for Image Recognition},
  author={He, Kaiming and Zhang, Xiangyu and Ren, Shaoqing and Sun, Jian},
  journal={arXiv preprint arXiv:1512.03385},
  year={2015}
}
```

#### Faster R-CNN
**Paper**: "Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks"
```bibtex
@article{ren2015faster,
  title={Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks},
  author={Ren, Shaoqing and He, Kaiming and Girshick, Ross and Sun, Jian},
  journal={arXiv preprint arXiv:1506.01497},
  year={2015}
}
```

### Acknowledgements

This project builds upon the pioneering work of many researchers and institutions:

- **Microsoft Research Asia (MSRA) Team**:
  - Kaiming He
  - Xiangyu Zhang
  - Shaoqing Ren
  - Jian Sun

- **Fast/Faster R-CNN Contributors**:
  - Ross Girshick (Microsoft Research)
  - Original Fast R-CNN team

Special thanks to all open-source contributors whose publicly shared implementations and improvements have provided valuable resources for research and development in the fields of computer vision and object detection.

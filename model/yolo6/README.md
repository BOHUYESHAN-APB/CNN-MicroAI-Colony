# YOLOv6 Colony Detection Model Test Results

## Overview
This document contains the test results of the YOLOv6-based colony detection model tested on a set of bacterial colony images.

## Test Dataset
The test dataset consists of 5 images with varying characteristics and challenges:

1. 2121.jpg
   - Actual colonies: 40
   - Merged colonies: 36
   - Issues: Colonies attached to medium edges, merging. Colony edges unclear and irregular.

2. 2021041310020608608.jpg
   - Actual colonies: 107
   - Merged colonies: 102
   - Issues: Standard image with watermark and text interference.

3. OIP-C.jpg
   - Actual colonies: 88
   - Merged colonies: 82
   - Issues: Relatively standard, some colonies attached to walls, some merging.

4. R-C.jpg
   - Actual colonies: 163
   - Merged colonies: 123
   - Issues: Low clarity, extensive colony merging, center-marked with another algorithm (low accuracy), culture medium has numerous impurities.

5. t019872959c62f44875.jpg
   - Actual colonies: 94
   - Merged colonies: 78
   - Issues: Colony merging, impure background, uneven culture medium, granular texture, reflective interference.

## Model Configuration
- Confidence threshold: 0.33
- Score threshold: 0.23
- NMS threshold: 0.28
- Size range: 11-88 pixels
- GPU acceleration: Enabled when available

## Test Results 
Results are saved in the 'test_outputs' directory with visualizations for each image:
- Colony positions marked with circles
- Color indicates confidence (Blue-Green gradient)
- Overlaid statistics including count, accuracy, and processing time

### Output Format
For each test image, the following metrics are computed:
- Colony count vs ground truth
- Error rates (compared to both actual and merged counts)
- Detection confidence scores
- Colony size distribution
- Processing time

## Visualizations
The test script generates visual results in 'test_outputs/':
- Detected colonies marked with colored circles
- Colony count and ground truth displayed
- Error rate percentage
- Processing time per image

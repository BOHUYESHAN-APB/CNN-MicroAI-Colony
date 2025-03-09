"""
Test Colony Detection Model
"""
import cv2
import torch
import numpy as np
from app.analysis_core import ColonyDetector
from pathlib import Path

def main():
    print("Testing colony detection...")
    try:
        # Initialize detector
        detector = ColonyDetector()
        print("Model loaded successfully!")
        
        # Test parameters
        params = {
            'confidence': 0.35,    # Higher confidence threshold
            'min_size': 12,       # Increased minimum size
            'max_size': 80,       # Reduced maximum size
            'nms_threshold': 0.3,  # Higher NMS threshold
            'score_threshold': 0.25, # Higher score threshold
            'use_gpu': torch.cuda.is_available()
        }

        # Print separator for better readability
        print("\n" + "="*50)
        print("DETECTION PARAMETERS")
        print("="*50)
        
        print("\nModel Parameters:")
        print("-" * 40)
        print(f"Confidence threshold: {params['confidence']}")
        print(f"Score threshold: {params['score_threshold']}")
        print(f"NMS threshold: {params['nms_threshold']}")
        print(f"Size range: {params['min_size']} - {params['max_size']} pixels")
        print(f"Using GPU: {params['use_gpu']}")
        
        # Test image path
        test_image = r"C:\Users\ETPau\Desktop\12\t019872959c62f44875.jpg"
        if not Path(test_image).exists():
            raise FileNotFoundError(f"Test image not found: {test_image}")
            
        
        print("\nAnalyzing test image...")
        results = detector.analyze(test_image, **params)
        
        print("\nDetection Results:")
        print(f"Found {results['count']} colonies")
        print(f"Colony density: {results['density']:.2f} per mm²")
        print(f"Area coverage: {results['area']:.2f}")
        print(f"Processing time: {results['time']:.2f} seconds")
        
        # Analyze detection statistics
        confidences = [colony['confidence'] for colony in results['colonies']]
        radii = [colony['radius'] for colony in results['colonies']]
        
        print("\n" + "="*50)
        print("DETECTION STATISTICS")
        print("="*50)
        print(f"Confidence Scores:")
        print(f"  - Average: {np.mean(confidences):.3f}")
        print(f"  - Range:   {min(confidences):.3f} to {max(confidences):.3f}")
        print(f"  - Std Dev: {np.std(confidences):.3f}")
        
        print(f"\nColony Sizes (diameter):")
        print(f"  - Average: {np.mean(radii)*2:.1f} pixels")
        print(f"  - Range:   {min(radii)*2:.1f} to {max(radii)*2:.1f} pixels")
        print(f"  - Std Dev: {np.std(radii)*2:.1f} pixels")

        # Create size distribution histogram
        size_hist, size_bins = np.histogram(radii, bins=10)
        print("\nSize Distribution (diameter):")
        print("-" * 40)
        max_count = max(size_hist)
        for i, count in enumerate(size_hist):
            size_range = f"{size_bins[i]*2:.1f}-{size_bins[i+1]*2:.1f}"
            bar = "#" * int(30 * count / max_count)
            print(f"  {size_range:>12} px | {bar:<30} | {count:3d}")
        
        # Visualize results
        image = cv2.imread(test_image)
        for colony in results['colonies']:
            # Use color coding based on confidence
            confidence = colony['confidence']
            color = (
                int(255 * (1 - confidence)),  # Blue
                int(255 * confidence),        # Green
                0                            # Red
            )
            
            cv2.circle(image, 
                      (colony['x'], colony['y']), 
                      colony['radius'], 
                      color, 
                      2)
            
            # Draw confidence score
            cv2.putText(image, 
                       f"{confidence:.2f}",
                       (colony['x'] - 20, colony['y'] - colony['radius'] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.5,
                       color,
                       1)
        
        # Save visualization
        output_path = "test_output.jpg"
        cv2.imwrite(output_path, image)
        print(f"\nVisualization saved to: {output_path}")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

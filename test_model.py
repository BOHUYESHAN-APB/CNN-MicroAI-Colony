"""
Test Colony Detection Model
"""
import cv2
import json
import torch
import numpy as np
from app.analysis_core import ColonyDetector
from pathlib import Path
from datetime import datetime

def main():
    print("Testing colony detection...")
    try:
        # Initialize detector
        detector = ColonyDetector()
        print("Model loaded successfully!")
        
        # Test parameters
        params = {
            'confidence': 0.33,    # Higher confidence for better precision
            'min_size': 11,       # Balanced minimum size
            'max_size': 88,       # Higher maximum for large colonies
            'nms_threshold': 0.28, # Higher NMS threshold for dense areas
            'score_threshold': 0.23, # Higher score threshold for quality
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
        
        # Load ground truth results
        with open("test-pic/result.json", "r", encoding='utf-8') as f:
            ground_truth = json.load(f)
        
        # Test images in test-pic folder
        test_dir = Path("test-pic")
        test_images = [f for f in test_dir.glob("*.jpg")]
        
        total_detection_count = 0
        total_ground_truth = 0
        total_time = 0
        all_results = []
        
        print("\nAnalyzing test images...")
        for img_path in test_images:
            print(f"\nProcessing {img_path.name}...")
            
            # Find ground truth data for current image
            gt_data = next((item for item in ground_truth if item["图片名称"] == img_path.name), None)
            if gt_data:
                gt_count = gt_data["实际菌落数"]
                merged_count = gt_data["合并菌落数"]
                print(f"Ground truth - Total: {gt_count}, Merged: {merged_count}")
            else:
                gt_count = 0
                merged_count = 0
                print("Warning: No ground truth data found for this image")
            total_ground_truth += gt_count
            
            # Analyze image
            results = detector.analyze(str(img_path), **params)
            total_detection_count += results['count']
            total_time += results['time']
            
            # Store results
            results['filename'] = img_path.name
            results['ground_truth'] = gt_count
            results['difference'] = results['count'] - gt_count
            
            # Calculate error rate (handle zero ground truth)
            if gt_count > 0:
                results['error_rate'] = abs(results['difference']) / gt_count * 100
            else:
                results['error_rate'] = float('inf') if results['count'] > 0 else 0
            all_results.append(results)
            
            # Print individual results
            print(f"Found {results['count']} colonies (Ground truth: {gt_count})")
            print(f"Difference: {results['difference']} ({results['error_rate']:.1f}% error)")
            print(f"Processing time: {results['time']:.2f} seconds")
        
        # Print summary
        print("\n" + "="*50)
        print("OVERALL RESULTS")
        print("="*50)
        print(f"Total detections: {total_detection_count}")
        print(f"Total ground truth: {total_ground_truth}")
        
        # Calculate average error rate (excluding infinite values)
        valid_errors = [r['error_rate'] for r in all_results if r['error_rate'] != float('inf')]
        if valid_errors:
            avg_error = sum(valid_errors) / len(valid_errors)
            print(f"Average error rate: {avg_error:.1f}%")
        else:
            print("No valid error rates to average")
            
        print(f"Total processing time: {total_time:.2f} seconds")
        
        # Print detailed results
        print("\nDetailed Results:")
        print("-" * 40)
        for result in all_results:
            print(f"{result['filename']}:")
            print(f"  Detected: {result['count']}")
            print(f"  Ground Truth: {result['ground_truth']}")
            print(f"  Error Rate: {result['error_rate']:.1f}% {'(N/A)' if result['error_rate'] == float('inf') else ''}")
        
        # Analyze and print detection statistics for each image
        print("\n" + "="*50)
        print("DETECTION STATISTICS (per image)")
        print("="*50)
        
        for result in all_results:
            print(f"\nImage: {result['filename']}")
            print("-" * 30)
            
            if result['colonies']: # Check if there are any detections
              confidences = [colony['confidence'] for colony in result['colonies']]
              radii = [colony['radius'] for colony in result['colonies']]
              
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
              print("-" * 30)
              max_count = max(size_hist)
              for i, count in enumerate(size_hist):
                  size_range = f"{size_bins[i]*2:.1f}-{size_bins[i+1]*2:.1f}"
                  bar = "#" * int(30 * count / max_count)
                  print(f"  {size_range:>12} px | {bar:<30} | {count:3d}")
            else:
                print("  No colonies detected.")

        # Save visualizations for each image
        output_dir = Path("test_outputs")
        output_dir.mkdir(exist_ok=True)
        
        print("\nSaving visualizations...")
        for result in all_results:
            # Load and process image
            image = cv2.imread(str(Path("test-pic") / result['filename']))
            if image is None:
                print(f"Warning: Could not load image {result['filename']}")
                continue
                
            # Draw colonies with confidence scores
            for colony in result['colonies']:
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
            
            # Add result summary
            info_text = [
                f"Colonies: {result['count']} (GT: {result['ground_truth']})",
                f"Error: {result['error_rate']:.1f}%",
                f"Time: {result['time']:.2f}s"
            ]
            
            y = 30
            for text in info_text:
                cv2.putText(image, text, (10, y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
                y += 30
            
            # Save output
            output_path = output_dir / f"result_{result['filename']}"
            cv2.imwrite(str(output_path), image)
            print(f"Saved visualization for {result['filename']}")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

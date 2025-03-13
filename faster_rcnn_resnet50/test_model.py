"""
Test Colony Detection Model
"""
import os
import sys
import unittest
import torch
import json
import cv2
import numpy as np
from pathlib import Path

# Add project root to Python path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import common logging setup
from app.utils.logger import setup_logging
from app.analysis_core import ColonyDetector

# Initialize logger
logger = setup_logging(log_file="test_output.log")

# Print Python path for debugging
logger.info(f"Python sys.path: {sys.path}")

class TestColonyDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ColonyDetector()
        self.test_image_dir = Path("test-pic")
        self.output_dir = Path("test_outputs")
        self.params = {
            'confidence': 0.33,
            'min_size': 11,
            'max_size': 88,
            'nms_threshold': 0.28,
            'score_threshold': 0.23,
            'use_gpu': torch.cuda.is_available()
        }
        self.output_dir.mkdir(exist_ok=True)

    def test_analyze_image(self):
        logger.info("Starting test_analyze_image...")
        
        # Verify test image exists and is readable
        test_image_path = self.test_image_dir / "2121.jpg"
        self.assertTrue(test_image_path.exists(), f"Test image not found: {test_image_path}")
        
        # Verify image can be read
        test_image = cv2.imread(str(test_image_path))
        self.assertIsNotNone(test_image, f"Failed to read image: {test_image_path}")
        logger.info(f"Test image loaded successfully: {test_image.shape}, {test_image.dtype}")

        try:
            # Run detection with debugging
            logger.info(f"Running analysis with parameters: {self.params}")
            self.detector._use_gpu = torch.cuda.is_available()
            logger.info(f"Using GPU: {self.detector._use_gpu}")
            
            results = self.detector.analyze(str(test_image_path), **self.params)
            logger.info(f"Analysis results: {results}")
            self.assertIsInstance(results, dict, "Analyze method should return a dictionary")
            self.assertIn("colonies", results, "Results should contain 'colonies' key")
            self.assertIsInstance(results["colonies"], list, "'colonies' should be a list")
            logger.info(f"Detected {len(results['colonies'])} colonies in {test_image_path.name}")

            # Basic sanity check on colony counts
            self.assertGreaterEqual(results["count"], 0, "Colony count should be non-negative")
            self.assertLessEqual(results["count"], 1000, "Colony count should be reasonably small")

            # Load ground truth results
            with open(self.test_image_dir / "result.json", "r", encoding='utf-8') as f:
                ground_truth = json.load(f)

            # Find ground truth data for current image
            gt_data = next((item for item in ground_truth if item["图片名称"] == Path(test_image_path).name), None)
            if gt_data:
                gt_count = gt_data["实际菌落数"]
                logger.info(f"Ground truth - Total: {gt_count}")
            else:
                gt_count = 0
                logger.warning(f"No ground truth data found for image: {Path(test_image_path).name}")

            # Calculate error rate
            difference = results['count'] - gt_count
            if gt_count > 0:
                error_rate = abs(difference) / gt_count * 100
            else:
                error_rate = float('inf') if results['count'] > 0 else 0
            logger.info(f"Difference: {difference} ({error_rate:.1f}% error)")

            # Assert that the error rate is within an acceptable range (e.g., 50%)
            self.assertLessEqual(error_rate, 50, "Error rate exceeds acceptable limit")

            # Save visualization
            self.save_visualization(test_image_path, results)

        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise

    def save_visualization(self, image_path, results):
        image = cv2.imread(str(image_path))
        if image is None:
            logger.error(f"Could not load image {image_path}")
            return

        # Draw colonies with confidence scores
        for colony in results['colonies']:
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
            f"Colonies: {results['count']}",
            f"Time: {results['time']:.2f}s"
        ]

        y = 30
        for text in info_text:
            cv2.putText(image, text, (10, y),
                       cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 0), 2)
            y += 30

        # Save output
        output_path = self.output_dir / f"result_{Path(image_path).name}"
        if cv2.imwrite(str(output_path), image):
            logger.info(f"Saved visualization to {output_path}")
        else:
            logger.error(f"Failed to save visualization for {image_path}")

if __name__ == "__main__":
    unittest.main()

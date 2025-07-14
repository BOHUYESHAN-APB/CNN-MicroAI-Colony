import onnx
from onnx_tf.backend import prepare
import tensorflow as tf
import os

def main():
    # --- Configuration ---
    onnx_model_path = "colony_detector.onnx"
    tflite_model_path = "colony_detector.tflite"
    # A temporary directory to store the intermediate TensorFlow SavedModel
    saved_model_dir = "saved_model"
    # --- End Configuration ---

    if not os.path.exists(onnx_model_path):
        print(f"Error: ONNX model not found at {onnx_model_path}")
        print("Please run convert_model.py first.")
        return

    print(f"Loading ONNX model from {onnx_model_path}...")
    # Load the ONNX model
    onnx_model = onnx.load(onnx_model_path)

    print("Preparing TensorFlow representation...")
    # Prepare the TensorFlow representation of the ONNX model
    tf_rep = prepare(onnx_model)

    print(f"Exporting to TensorFlow SavedModel format at {saved_model_dir}...")
    # Export the model to TensorFlow SavedModel format
    tf_rep.export_graph(saved_model_dir)

    print(f"Converting SavedModel to TensorFlow Lite format...")
    # Convert the SavedModel to a TFLite model
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    
    # Enable optimizations if needed (e.g., quantization)
    # converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    tflite_model = converter.convert()

    print(f"Saving TFLite model to {tflite_model_path}...")
    # Save the TFLite model to a file
    with open(tflite_model_path, 'wb') as f:
        f.write(tflite_model)

    print("Model conversion to TFLite completed successfully.")
    print(f"Saved at: {tflite_model_path}")

if __name__ == '__main__':
    main()
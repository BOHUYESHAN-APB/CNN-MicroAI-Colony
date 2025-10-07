# Android skeleton for MicroAI Colony

This is a minimal Android app skeleton that demonstrates how to capture a photo, save it to an internal app album, and where to place the ONNX model for inference.

Quick steps:

1. Copy the quantized ONNX to `android-app/app/src/main/assets/model.onnx`.
2. Open the `android-app` folder in Android Studio.
3. Build & run on a device (requires Camera permission).

Note: `MainActivity.kt` contains placeholders for ONNX inference. You will need to implement preprocessing and use ONNX Runtime API to load `assets/model.onnx` and run inference.

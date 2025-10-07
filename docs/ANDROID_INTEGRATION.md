# Android 集成指南（使用 ONNX Runtime Mobile）

推荐模型：`onnx model/checkpoint_epoch_31.quant.onnx`（经过动态量化，体积更小、适合移动端）。

要点：
- 使用 ONNX Runtime Mobile（AAR）集成到 Android 应用；或者使用 `onnxruntime-java` / `onnxruntime-android` 包。
- 预处理（与训练时一致）：
  - 将输入图片 resize 到 800x800
  - 将像素值归一化到 [0,1]
  - 扣除 mean [0.485,0.456,0.406]，除以 std [0.229,0.224,0.225]
  - 转换为 NCHW (1,3,800,800)，float32（若使用量化模型，输入仍然为 float32，量化器将对权重进行量化）
- 后处理：
  - ONNX 输出格式: boxes (1,N,4), labels (1,N), scores (1,N), num_detections (1,)
  - 对 scores 应用阈值（推荐 0.45），然后对剩余框运行 NMS（IoU 0.3）
  - 将 box 从 800x800 缩放回原图尺寸

示例 Gradle 依赖（在 `app/build.gradle` 中）：

```groovy
dependencies {
    implementation 'com.microsoft.onnxruntime:onnxruntime-android:1.15.1'
}
```

运行时注意：确保在前端线程外做推理（如使用 Executors），并在主线程渲染结果。

性能建议：如果量化模型在目标精度范围内表现良好，优先使用量化模型以降低内存和 CPU 负载。

更多：若需 AOT 或 GPU 加速，请参考 ONNX Runtime 官方文档以配置 NNAPI 或 GPU Provider。

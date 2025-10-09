Android app skeleton for MicroAI Colony detector

How to use

1. 默认会在构建前自动将仓库根目录中的 `onnx model/checkpoint_epoch_31.onnx` 拷贝到 `app/src/main/assets/model.onnx`。如需更换模型，请将目标文件放在同一目录并调整文件名或修改 `app/build.gradle` 中的拷贝任务。
2. 在 Android Studio 中打开 `android-app`，等待 Gradle 同步完成。
3. 如果运行按钮提示 `Module not specified`，在 Run/Debug Configurations 中选择 `Android App` → `app` 模块，或直接点击工具栏的绿色运行图标让 Studio 自动创建配置。
4. 连接真实设备并点击运行，授予相机权限。
5. 拍照后，应用会显示进度条并在相机捕获完成后运行 ONNX 推理。推理结果带注释的图片会保存到 `/data/data/<package>/files/album/annot_<timestamp>.jpg`，该路径会显示在界面上。界面还会展示“Last / Avg”推理耗时。

Notes

- 新的拍照流程使用 `FileProvider` 捕获全分辨率图片（保存在 `files/captures/`，随后复制到 `files/album/`）。
- 调整阈值或 NMS：界面上提供两个 SeekBar（默认 0.45 和 0.30）；代码端可在 `OnnxHelper.runInferenceAndSavePath` 中设置默认值。
- 不建议使用模拟器评估性能；请在 ARM64 实机上测试。
- 大模型可能会让 Gradle 构建占用更多内存，可在 `gradle.properties` 中调大 `org.gradle.jvmargs`。

图库支持点按图片进入全屏预览，并可一键分享。预览界面位于 `ImagePreviewActivity`。

应用会在 “Take Photo” 下方显示最近保存带注释图片的绝对路径，方便你在设备上定位该文件。

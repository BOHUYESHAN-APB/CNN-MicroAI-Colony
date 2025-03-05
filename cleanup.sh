#!/bin/bash

# 自动生成的清理脚本 - 使用前请仔细审查！

# 创建备份目录
mkdir -p ./backup/large_files

# 移动大文件到备份目录
mv ".\checkpoints\checkpoint_epoch_31.pth" "backup/large_files\checkpoint_epoch_31.pth"
mv ".\venv\Lib\site-packages\torch\lib\dnnl.lib" "backup/large_files\dnnl.lib"

# 删除临时文件
rm -f ".\venv\Lib\site-packages\torch\lib\cublasLt64_11.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cudnn_adv64_9.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cudnn_engines_precompiled64_9.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cudnn_ops64_9.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cufft64_10.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cusolver64_11.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cusolverMg64_11.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cusparse64_11.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\torch_cpu.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\torch_cuda.dll"
rm -f ".\venv\Lib\site-packages\cv2\cv2.pyd"
rm -f ".\venv\Lib\site-packages\torch\lib\cublas64_11.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\cudnn_heuristic64_9.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\curand64_10.dll"
rm -f ".\venv\Lib\site-packages\3204bda914b7f2c6f497__mypyc.cp311-win_amd64.pyd"
rm -f ".\venv\Lib\site-packages\cv2\opencv_videoio_ffmpeg4110_64.dll"
rm -f ".\venv\Lib\site-packages\numpy.libs\libscipy_openblas64_-43e11ff0749b8cbe0a615c9cf6737e0e.dll"
rm -f ".\venv\Lib\site-packages\onnxruntime\capi\onnxruntime.dll"
rm -f ".\venv\Lib\site-packages\onnxruntime\capi\onnxruntime_pybind11_state.pyd"
rm -f ".\venv\Lib\site-packages\PyQt5\Qt5\bin\opengl32sw.dll"
rm -f ".\venv\Lib\site-packages\scipy.libs\libscipy_openblas-f07f5a5d207a3a47104dca54d6d0c86a.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\nvrtc64_112_0.dll"
rm -f ".\venv\Lib\site-packages\torch\lib\torch_python.dll"

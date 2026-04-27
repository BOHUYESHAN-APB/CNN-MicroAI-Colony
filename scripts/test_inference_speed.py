#!/usr/bin/env python3
"""树莓派推理速度测试脚本"""
import time
import sys
from pathlib import Path
import numpy as np
import cv2

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.pi_ctk.core.inference_service import InferenceService, InferenceRequest


def test_inference_speed(model_path, iterations=10, warmup=3):
    """测试推理速度"""
    print(f"模型路径: {model_path}")
    print(f"预热次数: {warmup}, 测试次数: {iterations}")

    # 创建推理服务
    service = InferenceService(model_path, intra_threads=4, inter_threads=1)
    if not service.start():
        print("❌ 推理服务启动失败")
        return

    print("✅ 推理服务启动成功")

    # 创建测试图像
    test_image = np.random.randint(0, 255, (1024, 1024, 3), dtype=np.uint8)

    # 预热
    print(f"\n预热中...")
    for i in range(warmup):
        req = InferenceRequest(
            request_id=f"warmup_{i}",
            source_path="test",
            source_type="test",
            source_bgr=test_image,
            threshold=0.4,
            nms_iou=0.3,
            high_conf_thr=0.7,
            model_name="test"
        )
        service.submit(req)
        time.sleep(0.1)
        while service.try_get_result():
            pass

    # 正式测试
    print(f"\n开始测试...")
    latencies = []

    for i in range(iterations):
        req = InferenceRequest(
            request_id=f"test_{i}",
            source_path="test",
            source_type="test",
            source_bgr=test_image,
            threshold=0.4,
            nms_iou=0.3,
            high_conf_thr=0.7,
            model_name="test"
        )

        t0 = time.perf_counter()
        service.submit(req)

        # 等待结果
        result = None
        while result is None:
            result = service.try_get_result()
            time.sleep(0.01)

        latency = (time.perf_counter() - t0) * 1000
        latencies.append(latency)
        print(f"  迭代 {i+1}/{iterations}: {latency:.1f}ms")

    service.stop()

    # 统计
    latencies = np.array(latencies)
    print(f"\n{'='*50}")
    print(f"性能统计:")
    print(f"  平均延迟: {latencies.mean():.1f}ms")
    print(f"  中位数:   {np.median(latencies):.1f}ms")
    print(f"  最小值:   {latencies.min():.1f}ms")
    print(f"  最大值:   {latencies.max():.1f}ms")
    print(f"  P90:      {np.percentile(latencies, 90):.1f}ms")
    print(f"  P95:      {np.percentile(latencies, 95):.1f}ms")
    print(f"{'='*50}")


if __name__ == "__main__":
    model_path = "onnx model/checkpoint_epoch_31.onnx"

    if len(sys.argv) > 1:
        model_path = sys.argv[1]

    if not Path(model_path).exists():
        print(f"❌ 模型文件不存在: {model_path}")
        sys.exit(1)

    test_inference_speed(model_path)

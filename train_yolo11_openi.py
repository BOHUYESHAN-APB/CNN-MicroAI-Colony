#!/usr/bin/env python3
"""YOLO11训练脚本 - 适配启智平台数据集挂载"""

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _bootstrap_ultralytics():
    repo_root = Path(__file__).resolve().parent
    candidate_roots = [
        repo_root / "openi-archive" / "ultralytics-YOLO11",
        repo_root,
    ]

    for candidate in candidate_roots:
        package_init = candidate / "ultralytics" / "__init__.py"
        if not package_init.exists():
            continue
        sys.path.insert(0, str(candidate))
        print(f"使用仓库内ultralytics: {candidate}")
        break

    try:
        from ultralytics import YOLO as _YOLO
    except ModuleNotFoundError as ex:
        if ex.name != "ultralytics":
            raise
        print("未找到ultralytics包，回退到 pip install ultralytics")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])
        from ultralytics import YOLO as _YOLO

    return _YOLO


YOLO = _bootstrap_ultralytics()


def _prepare_offline_ultralytics_fonts():
    """Avoid network font downloads in offline OpenI containers."""
    try:
        from matplotlib import font_manager
        from ultralytics.utils import USER_CONFIG_DIR
        from ultralytics.utils import checks as checks_mod

        font_dir = Path(USER_CONFIG_DIR)
        font_dir.mkdir(parents=True, exist_ok=True)

        system_fonts = [Path(p) for p in font_manager.findSystemFonts()]
        preferred_names = [
            "Arial.ttf",
            "Arial Unicode.ttf",
            "Arial Unicode MS.ttf",
            "DejaVuSans.ttf",
            "LiberationSans-Regular.ttf",
            "NotoSans-Regular.ttf",
            "NotoSansCJK-Regular.ttc",
            "NotoSansCJK-Regular.otf",
        ]

        source_font = None
        for preferred in preferred_names:
            source_font = next((p for p in system_fonts if p.name == preferred), None)
            if source_font is not None:
                break

        def _offline_check_font(font="Arial.ttf"):
            name = Path(font).name
            target = font_dir / name
            if target.exists():
                return target

            direct_match = next((p for p in system_fonts if p.name == name), None)
            if direct_match is not None:
                return direct_match

            if source_font is not None:
                if not target.exists():
                    shutil.copy2(source_font, target)
                    print(f"离线字体兜底: {source_font.name} -> {target}")
                return target

            fallback = Path(font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans")))
            if fallback.exists():
                return fallback
            return target

        for target_name in ("Arial.ttf", "Arial.Unicode.ttf"):
            prepared = _offline_check_font(target_name)
            print(f"字体检查: {target_name} -> {prepared}")

        checks_mod.check_font = _offline_check_font
        try:
            import ultralytics.data.utils as data_utils_mod

            data_utils_mod.check_font = _offline_check_font
        except Exception as ex:
            print(f"补丁 data.utils.check_font 失败: {ex}")
    except Exception as ex:
        print(f"离线字体准备失败: {ex}")


def _prepare_c2net_context():
    try:
        context_mod = importlib.import_module("c2net.context")
        prepare_fn = getattr(context_mod, "prepare", None)
        if callable(prepare_fn):
            ctx = prepare_fn()
            print(f"c2net code_path: {getattr(ctx, 'code_path', '')}")
            print(f"c2net dataset_path: {getattr(ctx, 'dataset_path', '')}")
            print(f"c2net output_path: {getattr(ctx, 'output_path', '')}")
            return ctx
    except Exception as ex:
        print(f"c2net.context加载失败: {ex}")
    return None


def find_dataset_yaml(dataset_name=None, ctx=None):
    """查找数据集配置文件 - 适配启智平台挂载路径"""

    search_paths = []

    dataset_path = getattr(ctx, "dataset_path", "") if ctx is not None else ""
    if dataset_path:
        search_paths.append(Path(str(dataset_path)))
        print(f"c2net数据集路径: {dataset_path}")

    # 环境变量指定的路径
    if "OPENI_DATASET_PATH" in os.environ:
        search_paths.insert(0, Path(os.environ["OPENI_DATASET_PATH"]))

    # 备用搜索路径
    search_paths.extend([
        Path("/cache/dataset"),
        Path("/dataset"),
        Path("/home/work/user-job-dir/inputs/data"),
        Path("/userhome"),
        Path.cwd(),
    ])

    # 查找data.yaml
    print(f"搜索路径: {[str(p) for p in search_paths]}")
    for base_path in search_paths:
        if not base_path.exists():
            print(f"  路径不存在: {base_path}")
            continue

        print(f"  检查路径: {base_path}")

        # 直接查找
        yaml_path = base_path / "data.yaml"
        if yaml_path.exists():
            print(f"OK 找到数据集配置: {yaml_path}")
            return yaml_path

        # 在子目录中查找（一级）
        try:
            for subdir in base_path.iterdir():
                if not subdir.is_dir():
                    continue
                print(f"    检查子目录: {subdir.name}")

                # 检查一级子目录
                if dataset_name and subdir.name == dataset_name:
                    yaml_path = subdir / "data.yaml"
                    if yaml_path.exists():
                        print(f"OK 找到数据集配置: {yaml_path}")
                        return yaml_path
                elif not dataset_name:
                    yaml_path = subdir / "data.yaml"
                    if yaml_path.exists():
                        print(f"OK 找到数据集配置: {yaml_path}")
                        return yaml_path

                # 检查二级子目录（数据集仓库/数据集文件夹/data.yaml）
                try:
                    for subsubdir in subdir.iterdir():
                        if not subsubdir.is_dir():
                            continue
                        print(f"      检查二级子目录: {subdir.name}/{subsubdir.name}")
                        if dataset_name and subsubdir.name == dataset_name:
                            yaml_path = subsubdir / "data.yaml"
                            if yaml_path.exists():
                                print(f"OK 找到数据集配置: {yaml_path}")
                                return yaml_path
                        elif not dataset_name:
                            yaml_path = subsubdir / "data.yaml"
                            if yaml_path.exists():
                                print(f"OK 找到数据集配置: {yaml_path}")
                                return yaml_path
                except Exception as e:
                    pass
        except Exception as e:
            print(f"    遍历失败: {e}")

    raise FileNotFoundError(
        f"未找到data.yaml配置文件 (dataset_name={dataset_name})。\n"
        f"搜索路径: {[str(p) for p in search_paths]}"
    )


def main():
    os.environ.setdefault("YOLO_OFFLINE", "true")
    _prepare_offline_ultralytics_fonts()

    ctx = _prepare_c2net_context()

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--dataset-name', type=str, default=None, help='数据集文件夹名称')
        args, unknown = parser.parse_known_args()

        if unknown:
            print(f"忽略平台注入的额外参数: {unknown}")

        print("=" * 60)
        print("YOLO11 训练 - 启智平台")
        print("=" * 60)

        # 设置国内镜像加速模型下载
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

        # 查找数据集
        data_yaml = find_dataset_yaml(args.dataset_name, ctx=ctx)
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    # 读取配置确认
    with open(data_yaml, 'r', encoding='utf-8') as f:
        print("\n数据集配置:")
        yaml_content = f.read()
        print(yaml_content)

    # 修正data.yaml中的path为实际挂载路径
    import yaml
    with open(data_yaml, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)

    # 更新path为数据集实际路径
    data_config['path'] = str(data_yaml.parent)

    # 写回临时文件
    temp_yaml = Path('/tmp/data_fixed.yaml')
    with open(temp_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f)

    print(f"\n修正后的数据集路径: {data_config['path']}")
    data_yaml = temp_yaml

    # 加载YOLO11n模型（使用国内镜像或本地文件）
    print("\n加载YOLO11n模型...")
    model_path = "yolo11n.pt"

    # 尝试从ModelScope镜像下载
    if not Path(model_path).exists():
        print("从ModelScope下载预训练模型...")
        try:
            import urllib.request
            model_url = "https://modelscope.cn/models/AI-ModelScope/yolo11/resolve/master/yolo11n.pt"
            urllib.request.urlretrieve(model_url, model_path)
            print(f"OK 下载完成: {model_path}")
        except Exception as e:
            print(f"ModelScope下载失败: {e}")
            print("尝试直接加载（可能失败）...")

    model = YOLO(model_path)

    # 训练配置
    print("\n开始训练...")
    results = model.train(
        data=str(data_yaml),
        epochs=80,              # 80轮避免过拟合
        imgsz=640,              # 输入尺寸
        batch=16,               # 批次大小（根据GPU调整）
        device=0,               # 使用GPU 0

        # 优化器配置
        optimizer='AdamW',
        lr0=0.001,              # 初始学习率
        lrf=0.01,               # 最终学习率因子
        momentum=0.937,
        weight_decay=0.0005,

        # 数据增强
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=30,             # 旋转
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,

        # 其他配置
        patience=20,            # 早停
        save=True,
        save_period=10,         # 每10轮保存一次
        project='runs/colony_detection',
        name='yolo11n_colony',
        exist_ok=True,

        # 验证
        val=True,
        plots=False,            # 禁用绘图避免字体下载
    )

    # 训练完成
    print("\n" + "=" * 60)
    print("训练完成！")
    print(f"最佳模型: {model.trainer.best}")
    print(f"mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"mAP50-95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")
    print("=" * 60)

    # 导出ONNX
    print("\n导出ONNX模型...")
    model.export(format='onnx', imgsz=640, simplify=True)
    print("✓ ONNX模型已导出")

    # 复制模型到输出目录
    output_path = getattr(ctx, 'output_path', None) if ctx is not None else None
    if output_path:
        import shutil
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        best_pt = Path(model.trainer.best)
        best_onnx = best_pt.parent / 'best.onnx'

        shutil.copy2(best_pt, output_dir / 'yolo11n_colony_best.pt')
        shutil.copy2(best_onnx, output_dir / 'yolo11n_colony_best.onnx')

        print(f"\n✓ 模型已复制到输出目录: {output_dir}")
        print(f"  - yolo11n_colony_best.pt")
        print(f"  - yolo11n_colony_best.onnx")


if __name__ == "__main__":
    main()

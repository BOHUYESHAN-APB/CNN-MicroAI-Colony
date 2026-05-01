"""YOLO11 training entrypoint for OpenI."""

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


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


def find_dataset_yaml(dataset_name='MIC-all', ctx=None):
    """Find data.yaml from OpenI mounted datasets."""
    search_paths = []

    dataset_path = getattr(ctx, "dataset_path", "") if ctx is not None else ""
    if dataset_path:
        search_paths.append(Path(str(dataset_path)))
        print(f"c2net数据集路径: {dataset_path}")

    search_paths.extend([
        Path("/tmp/dataset"),
        Path("/cache/dataset"),
        Path("/dataset"),
        Path("/home/work/user-job-dir/inputs/data"),
    ])

    print(f"搜索路径: {[str(p) for p in search_paths]}")
    for base_path in search_paths:
        if not base_path.exists():
            continue
        print(f"  检查路径: {base_path}")

        direct_yaml = base_path / "data.yaml"
        if direct_yaml.exists():
            print(f"OK 找到数据集配置: {direct_yaml}")
            return direct_yaml

        for subdir in base_path.iterdir():
            if not subdir.is_dir():
                continue
            print(f"    检查子目录: {subdir.name}")
            if subdir.name == dataset_name:
                yaml_path = subdir / "data.yaml"
                if yaml_path.exists():
                    print(f"OK 找到数据集配置: {yaml_path}")
                    return yaml_path

            nested_yaml = subdir / "data.yaml"
            if nested_yaml.exists() and dataset_name in {subdir.name, "", None}:
                print(f"OK 找到数据集配置: {nested_yaml}")
                return nested_yaml

            try:
                for subsubdir in subdir.iterdir():
                    if not subsubdir.is_dir():
                        continue
                    print(f"      检查二级子目录: {subdir.name}/{subsubdir.name}")
                    yaml_path = subsubdir / "data.yaml"
                    if not yaml_path.exists():
                        continue
                    if dataset_name and subsubdir.name != dataset_name:
                        continue
                    print(f"OK 找到数据集配置: {yaml_path}")
                    return yaml_path
            except Exception:
                continue

    raise FileNotFoundError(f"未找到数据集 {dataset_name}")


def train_model(dataset_name, model_name, nc, class_names, epochs, ctx=None):
    """Train a single YOLO model."""
    print("\n" + "=" * 60)
    print(f"开始训练: {model_name}")
    print(f"数据集: {dataset_name}, 类别数: {nc}, 训练轮数: {epochs}")
    print("=" * 60)

    # 查找数据集
    data_yaml_path = find_dataset_yaml(dataset_name, ctx=ctx)

    # 修正data.yaml路径
    with open(data_yaml_path, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)

    data_config['path'] = str(data_yaml_path.parent)
    data_config['nc'] = nc
    data_config['names'] = class_names

    temp_yaml = Path(f'/tmp/data_{model_name}.yaml')
    with open(temp_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f)

    # 加载模型
    model_path = "yolo11n.pt"
    if not Path(model_path).exists():
        print("从ModelScope下载预训练模型...")
        import urllib.request
        model_url = "https://modelscope.cn/models/AI-ModelScope/yolo11/resolve/master/yolo11n.pt"
        urllib.request.urlretrieve(model_url, model_path)

    model = YOLO(model_path)

    # 训练
    results = model.train(
        data=str(temp_yaml),
        epochs=epochs,
        imgsz=640,
        batch=16,
        device=0,
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=30,
        translate=0.1,
        scale=0.5,
        flipud=0.5,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        patience=30,
        save=True,
        save_period=-1,  # 保存所有epoch
        project='runs/colony_detection',
        name=model_name,
        exist_ok=True,
        val=True,
        plots=False,
    )

    # 导出ONNX (best模型)
    print(f"\n导出{model_name} ONNX...")
    model.export(format='onnx', imgsz=640, simplify=True)

    output_path = getattr(ctx, "output_path", None) if ctx is not None else None
    if output_path:
        try:
            import shutil

            output_dir = Path(output_path) / model_name
            output_dir.mkdir(parents=True, exist_ok=True)

            weights_dir = Path(model.trainer.best).parent

            for ckpt in weights_dir.glob('*.pt'):
                if ckpt.name not in ['best.pt', 'last.pt']:
                    shutil.copy2(ckpt, output_dir / ckpt.name)

            shutil.copy2(weights_dir / 'best.pt', output_dir / 'best.pt')
            shutil.copy2(weights_dir / 'best.onnx', output_dir / 'best.onnx')
            if (weights_dir / 'last.pt').exists():
                shutil.copy2(weights_dir / 'last.pt', output_dir / 'last.pt')

            if (weights_dir / 'last.pt').exists():
                last_model = YOLO(str(weights_dir / 'last.pt'))
                last_model.export(format='onnx', imgsz=640, simplify=True)
                shutil.copy2(weights_dir / 'last.onnx', output_dir / 'last.onnx')

            results_csv = weights_dir.parent / 'results.csv'
            if results_csv.exists():
                shutil.copy2(results_csv, output_dir / 'results.csv')

            args_yaml = weights_dir.parent / 'args.yaml'
            if args_yaml.exists():
                shutil.copy2(args_yaml, output_dir / 'args.yaml')

            config_info = {
                'model_name': model_name,
                'dataset': dataset_name,
                'nc': nc,
                'names': class_names,
                'epochs': epochs,
                'batch_size': 16,
                'imgsz': 640,
                'mAP50': float(results.results_dict.get('metrics/mAP50(B)', 0)),
                'mAP50-95': float(results.results_dict.get('metrics/mAP50-95(B)', 0)),
                'best_epoch': model.trainer.best_epoch if hasattr(model.trainer, 'best_epoch') else 'N/A',
            }
            with open(output_dir / 'model_info.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config_info, f, allow_unicode=True)

            print(f"\n✓ {model_name} 已保存到: {output_dir}")
            print("  - 所有checkpoint (epoch_*.pt)")
            print("  - best.pt + best.onnx (最佳模型)")
            print("  - last.pt + last.onnx (最后一轮)")
            print("  - results.csv (训练曲线)")
            print("  - args.yaml (训练参数)")
            print("  - model_info.yaml (模型信息+类别映射)")
        except Exception as ex:
            print(f"保存到输出目录失败: {ex}")

    return results


def main():
    os.environ.setdefault("YOLO_OFFLINE", "true")
    _prepare_offline_ultralytics_fonts()

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-name', type=str, default='MIC-all', help='数据集文件夹名称')
    parser.add_argument('--epochs', type=int, default=120, help='训练轮数')
    args, unknown = parser.parse_known_args()

    if unknown:
        print(f"忽略平台注入的额外参数: {unknown}")

    ctx = _prepare_c2net_context()

    print("=" * 60)
    print("YOLO11 训练 - MIC-all数据集")
    print("=" * 60)

    # 训练完整版 (7类)
    train_model(
        dataset_name=args.dataset_name,
        model_name='yolo11n_advanced',
        nc=7,
        class_names=['B-subtilis', 'C-albicans', 'Contamination', 'Defect', 'E-coli', 'P-aeruginosa', 'S-aureus'],
        epochs=args.epochs,
        ctx=ctx,
    )

    print("\n" + "=" * 60)
    print("✓ 训练完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

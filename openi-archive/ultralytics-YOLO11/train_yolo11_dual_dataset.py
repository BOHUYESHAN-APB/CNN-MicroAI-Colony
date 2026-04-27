"""
YOLO11训练脚本 - 双数据集版本
支持同时训练基础版(5类)和完整版(7类)
"""
import sys
from pathlib import Path
import yaml

# 添加ultralytics到路径
sys.path.insert(0, str(Path(__file__).parent))

from ultralytics import YOLO

try:
    from c2net import context as c2net_context
    USE_C2NET = True
except ImportError:
    USE_C2NET = False
    print("警告: c2net未安装，使用本地模式")


def train_model(dataset_name, model_name, nc, class_names, epochs):
    """训练单个模型"""
    print("\n" + "=" * 60)
    print(f"开始训练: {model_name}")
    print(f"数据集: {dataset_name}, 类别数: {nc}, 训练轮数: {epochs}")
    print("=" * 60)

    # 查找数据集
    if USE_C2NET:
        dataset_root = Path('/tmp/dataset')
    else:
        dataset_root = Path('/dataset')

    search_paths = [
        dataset_root,
        Path('/cache/dataset'),
        Path('/dataset'),
        Path('/home/work/user-job-dir/inputs/data'),
    ]

    data_yaml_path = None
    for base in search_paths:
        if not base.exists():
            continue
        candidate = base / dataset_name / 'data.yaml'
        if candidate.exists():
            data_yaml_path = candidate
            print(f"✓ 找到数据集: {data_yaml_path}")
            break

    if not data_yaml_path:
        raise FileNotFoundError(f"未找到数据集 {dataset_name}")

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

    # 复制到输出目录
    if USE_C2NET and c2net_context.output_path:
        import shutil
        output_dir = Path(c2net_context.output_path) / model_name
        output_dir.mkdir(parents=True, exist_ok=True)

        weights_dir = Path(model.trainer.best).parent

        # 复制所有checkpoint
        for ckpt in weights_dir.glob('*.pt'):
            if ckpt.name not in ['best.pt', 'last.pt']:
                shutil.copy2(ckpt, output_dir / ckpt.name)

        # 复制best和last模型
        shutil.copy2(weights_dir / 'best.pt', output_dir / 'best.pt')
        shutil.copy2(weights_dir / 'best.onnx', output_dir / 'best.onnx')
        if (weights_dir / 'last.pt').exists():
            shutil.copy2(weights_dir / 'last.pt', output_dir / 'last.pt')

        # 导出last模型为ONNX
        if (weights_dir / 'last.pt').exists():
            last_model = YOLO(str(weights_dir / 'last.pt'))
            last_model.export(format='onnx', imgsz=640, simplify=True)
            shutil.copy2(weights_dir / 'last.onnx', output_dir / 'last.onnx')

        # 复制训练结果和配置
        results_csv = weights_dir.parent / 'results.csv'
        if results_csv.exists():
            shutil.copy2(results_csv, output_dir / 'results.csv')

        args_yaml = weights_dir.parent / 'args.yaml'
        if args_yaml.exists():
            shutil.copy2(args_yaml, output_dir / 'args.yaml')

        # 保存模型信息
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
        with open(output_dir / 'model_info.yaml', 'w') as f:
            yaml.dump(config_info, f)

        print(f"\n✓ {model_name} 已保存到: {output_dir}")
        print(f"  - 所有checkpoint (epoch_*.pt)")
        print(f"  - best.pt + best.onnx (最佳模型)")
        print(f"  - last.pt + last.onnx (最后一轮)")
        print(f"  - results.csv (训练曲线)")
        print(f"  - args.yaml (训练参数)")
        print(f"  - model_info.yaml (模型信息+类别映射)")

    return results


def main():
    print("=" * 60)
    print("YOLO11 双数据集训练")
    print("=" * 60)

    # 训练基础版 (5类) - 小数据集，更多轮次
    train_model(
        dataset_name='MIC-basic',
        model_name='yolo11n_basic',
        nc=5,
        class_names=['B-subtilis', 'C-albicans', 'E-coli', 'P-aeruginosa', 'S-aureus'],
        epochs=150
    )

    # 训练完整版 (7类) - 大数据集
    train_model(
        dataset_name='MIC-all',
        model_name='yolo11n_advanced',
        nc=7,
        class_names=['B-subtilis', 'C-albicans', 'Contamination', 'Defect', 'E-coli', 'P-aeruginosa', 'S-aureus'],
        epochs=120
    )

    print("\n" + "=" * 60)
    print("✓ 所有训练完成！")
    print("预计总时间: ~8-10小时")
    print("=" * 60)


if __name__ == "__main__":
    main()

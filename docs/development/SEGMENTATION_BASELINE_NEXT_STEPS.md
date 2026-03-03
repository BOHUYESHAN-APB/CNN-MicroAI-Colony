# Segmentation Baseline: Immediate Next Commands

This runbook gives direct commands for the next training stage after category cleanup.

## 1) Prepare clean detection labels (already implemented)

```bash
python scripts/audit_remap_coco_categories.py \
  --dataset-root "E:\train\S. Aureus Plates.v4-1000-x-1000-training-version.coco-mmdetection" \
  --splits train valid test \
  --output-root "E:\train\S. Aureus Plates.v4-1000-x-1000-training-version.coco-mmdetection.remapped" \
  --report-json "E:\CODE\CNN-MicroAI-Colony\test_outputs\saureus_eval\remap_audit_report.json"
```

If you need local image copies in the remapped tree for direct evaluation:

```bash
python scripts/audit_remap_coco_categories.py \
  --dataset-root "E:\train\S. Aureus Plates.v4-1000-x-1000-training-version.coco-mmdetection" \
  --splits test \
  --copy-images \
  --output-root "E:\train\S. Aureus Plates.v4-1000-x-1000-training-version.coco-mmdetection.remapped_with_images" \
  --report-json "E:\CODE\CNN-MicroAI-Colony\test_outputs\saureus_eval\remap_audit_report_with_images.json"
```

## 2) Fast smoke-eval on remapped test split (no retraining)

```bash
python scripts/eval_coco_onnx_latency.py \
  --dataset-root "E:\train\S. Aureus Plates.v4-1000-x-1000-training-version.coco-mmdetection.remapped_with_images" \
  --split test \
  --model "E:\CODE\CNN-MicroAI-Colony\onnx model\checkpoint_epoch_31.static_qdq.onnx" \
  --max-images 20 \
  --out-csv "E:\CODE\CNN-MicroAI-Colony\test_outputs\saureus_eval\smoke_remap_eval.csv" \
  --out-json "E:\CODE\CNN-MicroAI-Colony\test_outputs\saureus_eval\smoke_remap_eval.json"
```

## 3) Segmentation-capable baseline fine-tune (recommended path)

Use an instance-segmentation COCO dataset (one of the `*.coco-segmentation` datasets under `E:\train`) and fine-tune Mask R-CNN in MMDetection.

### 3.1 Install environment

```bash
pip install -U openmim
mim install "mmengine>=0.10.0" "mmcv>=2.0.0" "mmdet>=3.0.0"
```

### 3.2 Create dataset links (example)

```bash
mkdir "E:\train\seg_work\dataset"
```

Place your selected segmentation dataset as:

- `E:\train\seg_work\dataset\train\`
- `E:\train\seg_work\dataset\valid\`
- `E:\train\seg_work\dataset\test\`
- each split includes `_annotations.coco.json`

### 3.3 Train Mask R-CNN baseline

```bash
python -m mmdet.tools.train \
  "configs/mask_rcnn/mask-rcnn_r50_fpn_1x_coco.py" \
  --cfg-options \
  train_dataloader.dataset.ann_file="E:/train/seg_work/dataset/train/_annotations.coco.json" \
  train_dataloader.dataset.data_root="E:/train/seg_work/dataset/train/" \
  val_dataloader.dataset.ann_file="E:/train/seg_work/dataset/valid/_annotations.coco.json" \
  val_dataloader.dataset.data_root="E:/train/seg_work/dataset/valid/" \
  test_dataloader.dataset.ann_file="E:/train/seg_work/dataset/test/_annotations.coco.json" \
  test_dataloader.dataset.data_root="E:/train/seg_work/dataset/test/" \
  model.roi_head.bbox_head.num_classes=1 \
  model.roi_head.mask_head.num_classes=1 \
  train_cfg.max_epochs=24 \
  default_hooks.checkpoint.interval=1 \
  work_dir="E:/train/seg_work/maskrcnn_r50_colony"
```

### 3.4 Evaluate checkpoint (bbox + segm)

```bash
python -m mmdet.tools.test \
  "configs/mask_rcnn/mask-rcnn_r50_fpn_1x_coco.py" \
  "E:/train/seg_work/maskrcnn_r50_colony/epoch_24.pth" \
  --cfg-options \
  test_dataloader.dataset.ann_file="E:/train/seg_work/dataset/test/_annotations.coco.json" \
  test_dataloader.dataset.data_root="E:/train/seg_work/dataset/test/" \
  model.roi_head.bbox_head.num_classes=1 \
  model.roi_head.mask_head.num_classes=1 \
  --eval bbox segm
```

## 4) Pi deployment checkpoint

After you have a validated segmentation checkpoint, export to ONNX and run latency/accuracy checks on Pi before integrating into the CTk app pipeline.

"""
Colony detection model configuration — switchable variants
菌落检测模型配置 — 可切换变体

Variants:
  - faster_rcnn_baseline: 两阶段 Faster R-CNN (历史基线 / 对照组)
  - retinanet_pi:          单阶段 RetinaNet 高精主线 (论文主实验 + Pi 部署候选)
  - retinanet_rt:          单阶段 RetinaNet 实时备线 (低算力 fallback)

Usage:
  VARIANT = "retinanet_pi"   # 切换此处选择变体
  python src/train.py configs/faster_rcnn_colony.py

NOTE: retinanet_pi / retinanet_rt 配置来自交接文档 §10.3 / §10.4，
      已适配当前 MMDetection 框架 (PyTorch)。
      历史 MindSpore 路线已废弃，不再在此配置中保留。
"""

# ============================================================================
# Variant selector — 改此处切换模型
# ============================================================================
VARIANT = "faster_rcnn_baseline"  # faster_rcnn_baseline | retinanet_pi | retinanet_rt

# ============================================================================
# Per-variant model definitions
# ============================================================================

if VARIANT == "faster_rcnn_baseline":
    # --- 两阶段 Faster R-CNN 基线 (历史对照) ---
    model = dict(
        type="FasterRCNN",
        backbone=dict(
            type="ResNet",
            depth=50,
            num_stages=4,
            out_indices=(0, 1, 2, 3),
            frozen_stages=1,
            norm_cfg=dict(type="BN", requires_grad=True),
            norm_eval=True,
            style="pytorch",
            init_cfg=dict(type="Pretrained", checkpoint="torchvision://resnet50"),
            plugins=[
                dict(
                    cfg=dict(type="ContextBlock", ratio=1.0 / 4),
                    stages=(False, True, True, True),
                    position="after_conv3",
                )
            ],
        ),
        neck=dict(
            type="FPN", in_channels=[256, 512, 1024, 2048], out_channels=256, num_outs=5
        ),
        rpn_head=dict(
            type="RPNHead",
            in_channels=256,
            feat_channels=256,
            anchor_generator=dict(
                type="AnchorGenerator",
                scales=[2, 4, 8, 16],
                ratios=[0.5, 1.0, 1.5],
                strides=[4, 8, 16, 32, 64],
            ),
            bbox_coder=dict(
                type="DeltaXYWHBBoxCoder",
                target_means=[0.0, 0.0, 0.0, 0.0],
                target_stds=[1.0, 1.0, 1.0, 1.0],
            ),
            loss_cls=dict(type="CrossEntropyLoss", use_sigmoid=True, loss_weight=1.0),
            loss_bbox=dict(type="SmoothL1Loss", beta=1.0 / 9.0, loss_weight=1.0),
        ),
        roi_head=dict(
            type="StandardRoIHead",
            bbox_roi_extractor=dict(
                type="SingleRoIExtractor",
                roi_layer=dict(type="RoIAlign", output_size=7, sampling_ratio=0),
                out_channels=256,
                featmap_strides=[4, 8, 16, 32],
            ),
            bbox_head=dict(
                type="Shared2FCBBoxHead",
                in_channels=256,
                fc_out_channels=1024,
                roi_feat_size=7,
                num_classes=1,
                bbox_coder=dict(
                    type="DeltaXYWHBBoxCoder",
                    target_means=[0.0, 0.0, 0.0, 0.0],
                    target_stds=[0.1, 0.1, 0.2, 0.2],
                ),
                reg_class_agnostic=False,
                loss_cls=dict(
                    type="CrossEntropyLoss", use_sigmoid=False, loss_weight=1.0
                ),
                loss_bbox=dict(type="SmoothL1Loss", beta=1.0, loss_weight=1.0),
            ),
        ),
        train_cfg=dict(
            rpn=dict(
                assigner=dict(
                    type="MaxIoUAssigner",
                    pos_iou_thr=0.7,
                    neg_iou_thr=0.3,
                    min_pos_iou=0.3,
                    match_low_quality=True,
                    ignore_iof_thr=-1,
                ),
                sampler=dict(
                    type="RandomSampler",
                    num=256,
                    pos_fraction=0.5,
                    neg_pos_ub=-1,
                    add_gt_as_proposals=False,
                ),
                allowed_border=-1,
                pos_weight=-1,
                debug=False,
            ),
            rpn_proposal=dict(
                nms_pre=2000,
                max_per_img=1000,
                nms=dict(type="nms", iou_threshold=0.7),
                min_bbox_size=0,
            ),
            rcnn=dict(
                assigner=dict(
                    type="MaxIoUAssigner",
                    pos_iou_thr=0.5,
                    neg_iou_thr=0.5,
                    min_pos_iou=0.5,
                    match_low_quality=False,
                    ignore_iof_thr=-1,
                ),
                sampler=dict(
                    type="RandomSampler",
                    num=512,
                    pos_fraction=0.25,
                    neg_pos_ub=-1,
                    add_gt_as_proposals=True,
                ),
                pos_weight=-1,
                debug=False,
            ),
        ),
        test_cfg=dict(
            rpn=dict(
                nms_pre=1000,
                max_per_img=1000,
                nms=dict(type="nms", iou_threshold=0.7),
                min_bbox_size=0,
            ),
            rcnn=dict(
                score_thr=0.05, nms=dict(type="nms", iou_threshold=0.5), max_per_img=100
            ),
        ),
    )

elif VARIANT == "retinanet_pi":
    # --- 单阶段 RetinaNet 高精主线 (论文主实验 + Pi 部署候选) ---
    # 设计要点: ResNet-50 + FPN 256 + 4 层卷积 head, FocalLoss
    # ONNX 友好 (无 RoIAlign), 适合 ORT CPU 推理
    model = dict(
        type="RetinaNet",
        backbone=dict(
            type="ResNet",
            depth=50,
            num_stages=4,
            out_indices=(0, 1, 2, 3),
            frozen_stages=1,
            norm_cfg=dict(type="BN", requires_grad=True),
            norm_eval=True,
            style="pytorch",
            init_cfg=dict(type="Pretrained", checkpoint="torchvision://resnet50"),
        ),
        neck=dict(
            type="FPN",
            in_channels=[256, 512, 1024, 2048],
            out_channels=256,
            num_outs=5,
        ),
        bbox_head=dict(
            type="RetinaHead",
            num_classes=1,
            in_channels=256,
            stacked_convs=4,
            feat_channels=256,
            anchor_generator=dict(
                type="AnchorGenerator",
                octave_base_scale=4,
                scales_per_octade=3,
                ratios=[0.5, 1.0, 1.5],
                strides=[8, 16, 32, 64, 128],
            ),
            bbox_coder=dict(
                type="DeltaXYWHBBoxCoder",
                target_means=[0.0, 0.0, 0.0, 0.0],
                target_stds=[1.0, 1.0, 1.0, 1.0],
            ),
            loss_cls=dict(
                type="FocalLoss",
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=1.0,
            ),
            loss_bbox=dict(type="L1Loss", loss_weight=1.0),
        ),
        train_cfg=dict(
            assigner=dict(
                type="MaxIoUAssigner",
                pos_iou_thr=0.5,
                neg_iou_thr=0.4,
                min_pos_iou=0,
                ignore_iof_thr=-1,
            ),
            allowed_border=-1,
            pos_weight=-1,
            debug=False,
        ),
        test_cfg=dict(
            nms_pre=1000,
            min_bbox_size=0,
            score_thr=0.05,
            nms=dict(type="nms", iou_threshold=0.5),
            max_per_img=300,
        ),
    )

elif VARIANT == "retinanet_rt":
    # --- 单阶段 RetinaNet 实时备线 (低算力 fallback) ---
    # 设计要点: ResNet-18 + FPN 128 + 3 层卷积 head, 更轻量
    # 作为 retinanet_rt 延迟/内存超预算时的备用方案
    model = dict(
        type="RetinaNet",
        backbone=dict(
            type="ResNet",
            depth=18,
            num_stages=4,
            out_indices=(0, 1, 2, 3),
            frozen_stages=1,
            norm_cfg=dict(type="BN", requires_grad=True),
            norm_eval=True,
            style="pytorch",
            init_cfg=dict(type="Pretrained", checkpoint="torchvision://resnet18"),
        ),
        neck=dict(
            type="FPN",
            in_channels=[64, 128, 256, 512],
            out_channels=128,
            num_outs=5,
        ),
        bbox_head=dict(
            type="RetinaHead",
            num_classes=1,
            in_channels=128,
            stacked_convs=3,
            feat_channels=128,
            anchor_generator=dict(
                type="AnchorGenerator",
                octave_base_scale=4,
                scales_per_octade=3,
                ratios=[0.5, 1.0, 1.5],
                strides=[8, 16, 32, 64, 128],
            ),
            bbox_coder=dict(
                type="DeltaXYWHBBoxCoder",
                target_means=[0.0, 0.0, 0.0, 0.0],
                target_stds=[1.0, 1.0, 1.0, 1.0],
            ),
            loss_cls=dict(
                type="FocalLoss",
                use_sigmoid=True,
                gamma=2.0,
                alpha=0.25,
                loss_weight=1.0,
            ),
            loss_bbox=dict(type="L1Loss", loss_weight=1.0),
        ),
        train_cfg=dict(
            assigner=dict(
                type="MaxIoUAssigner",
                pos_iou_thr=0.5,
                neg_iou_thr=0.4,
                min_pos_iou=0,
                ignore_iof_thr=-1,
            ),
            allowed_border=-1,
            pos_weight=-1,
            debug=False,
        ),
        test_cfg=dict(
            nms_pre=800,
            min_bbox_size=0,
            score_thr=0.05,
            nms=dict(type="nms", iou_threshold=0.5),
            max_per_img=200,
        ),
    )

else:
    raise ValueError(
        f"Unknown VARIANT={VARIANT!r}. Use: faster_rcnn_baseline | retinanet_pi | retinanet_rt"
    )

# ============================================================================
# Per-variant pipeline / optimizer overrides
# ============================================================================

if VARIANT == "retinanet_rt":
    # 实时备线: 更小输入尺寸, 更少增强
    _train_img_scale = [(1024, 1024), (640, 640)]
    _test_img_scale = (640, 640)
else:
    # baseline + retinanet_pi: 标准多尺度
    _train_img_scale = [(1280, 1280), (800, 800)]
    _test_img_scale = (1280, 1280)

# Dataset configuration
dataset_type = "COCODataset"
data_root = "main_models_train/train/"
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True
)

train_pipeline = [
    dict(type="LoadImageFromFile"),
    dict(type="LoadAnnotations", with_bbox=True),
    dict(
        type="Resize",
        img_scale=_train_img_scale,
        multiscale_mode="range",
        keep_ratio=True,
    ),
    dict(
        type="AutoAugment",
        policies=[
            [
                dict(type="RandomRotate", prob=0.5, level=5),
                dict(type="BrightnessTransform", level=5),
            ],
            [dict(type="RandomContrast", prob=0.5), dict(type="Blur", prob=0.3)],
        ],
    ),
    dict(type="RandomFlip", flip_ratio=0.5),
    dict(type="Normalize", **img_norm_cfg),
    dict(type="Pad", size_divisor=32),
    dict(type="DefaultFormatBundle"),
    dict(type="Collect", keys=["img", "gt_bboxes", "gt_labels"]),
]

test_pipeline = [
    dict(type="LoadImageFromFile"),
    dict(
        type="MultiScaleFlipAug",
        img_scale=_test_img_scale,
        flip=False,
        transforms=[
            dict(type="Resize", keep_ratio=True),
            dict(type="RandomFlip"),
            dict(type="Normalize", **img_norm_cfg),
            dict(type="Pad", size_divisor=32),
            dict(type="ImageToTensor", keys=["img"]),
            dict(type="Collect", keys=["img"]),
        ],
    ),
]

data = dict(
    samples_per_gpu=2,
    workers_per_gpu=2,
    train=dict(
        type=dataset_type,
        ann_file=data_root + "train/_annotations.coco.json",
        img_prefix=data_root + "train",
        pipeline=train_pipeline,
    ),
    val=dict(
        type=dataset_type,
        ann_file=data_root + "valid/_annotations.coco.json",
        img_prefix=data_root + "valid",
        pipeline=test_pipeline,
    ),
    test=dict(
        type=dataset_type,
        ann_file=data_root + "test/_annotations.coco.json",
        img_prefix=data_root + "test",
        pipeline=test_pipeline,
    ),
)

# Training configuration
optimizer = dict(
    type="AdamW",
    lr=0.0001,
    betas=(0.9, 0.999),
    weight_decay=0.05,
    paramwise_cfg=dict(
        custom_keys={
            "absolute_pos_embed": dict(decay_mult=0.0),
            "relative_position_b bias_table": dict(decay_mult=0.0),
            "norm": dict(decay_mult=0.0),
        }
    ),
)
optimizer_config = dict(
    grad_clip=dict(max_norm=35, norm_type=2),
    type="Fp16OptimizerHook",
    loss_scale=dict(init_scale=512),
)
lr_config = dict(
    policy="step", warmup="linear", warmup_iters=500, warmup_ratio=0.001, step=[8, 11]
)
runner = dict(type="EpochBasedRunner", max_epochs=12)

# Runtime configuration
checkpoint_config = dict(
    interval=1, max_keep_ckpts=3, save_optimizer=True, save_last=True
)
log_config = dict(
    interval=50,
    hooks=[
        dict(type="TextLoggerHook"),
        dict(type="TensorboardLoggerHook"),
        dict(
            type="MMDetWandbHook",
            init_kwargs={
                "project": "colony-detection",
                "group": "faster-rcnn",
            },
            interval=50,
            log_checkpoint=True,
            log_checkpoint_metadata=True,
            num_eval_images=100,
        ),
    ],
)
custom_hooks = [dict(type="NumClassCheckHook")]
dist_params = dict(backend="nccl")
log_level = "INFO"
load_from = None
resume_from = None
workflow = [("train", 1)]
work_dir = "/root/autodl-tmp"  # 模型输出目录设置为/root/autodl-tmp

# Performance optimization
opencv_num_threads = 0
mp_start_method = "fork"
seed = 42
deterministic = True
cudnn_benchmark = True

# Auto-scaling config
auto_scale_lr = dict(enable=True, base_batch_size=16)

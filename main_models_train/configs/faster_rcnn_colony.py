"""
Faster R-CNN configuration for colony detection
用于菌落检测的Faster R-CNN配置
"""

# Model configuration
# 模型配置
model = dict(
    type='FasterRCNN',
    backbone=dict(
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(0, 1, 2, 3),
        frozen_stages=1,
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=True,
        style='pytorch',
        init_cfg=dict(type='Pretrained', checkpoint='torchvision://resnet50'),
        plugins=[
            dict(
                cfg=dict(type='ContextBlock', ratio=1./4),
                stages=(False, True, True, True),
                position='after_conv3'
            )
        ]
    ),
    neck=dict(
        type='FPN',
        in_channels=[256, 512, 1024, 2048],
        out_channels=256,
        num_outs=5
    ),
    rpn_head=dict(
        type='RPNHead',
        in_channels=256,
        feat_channels=256,
        # Optimized anchor sizes for colony detection
        anchor_generator=dict(
            type='AnchorGenerator',
            scales=[2, 4, 8, 16],  # Added smaller scale for tiny colonies
            ratios=[0.5, 1.0, 1.5],  # Added 1.5 ratio for oval colonies
            strides=[4, 8, 16, 32, 64]
        ),
        bbox_coder=dict(
            type='DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[1.0, 1.0, 1.0, 1.0]
        ),
        loss_cls=dict(
            type='CrossEntropyLoss',
            use_sigmoid=True,
            loss_weight=1.0
        ),
        loss_bbox=dict(
            type='SmoothL1Loss',
            beta=1.0 / 9.0,
            loss_weight=1.0
        )
    ),
    roi_head=dict(
        type='StandardRoIHead',
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(
                type='RoIAlign',
                output_size=7,
                sampling_ratio=0
            ),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]
        ),
        bbox_head=dict(
            type='Shared2FCBBoxHead',
            in_channels=256,
            fc_out_channels=1024,
            roi_feat_size=7,
            num_classes=1,  # Only colony class
            bbox_coder=dict(
                type='DeltaXYWHBBoxCoder',
                target_means=[0., 0., 0., 0.],
                target_stds=[0.1, 0.1, 0.2, 0.2]
            ),
            reg_class_agnostic=False,
            loss_cls=dict(
                type='CrossEntropyLoss',
                use_sigmoid=False,
                loss_weight=1.0
            ),
            loss_bbox=dict(
                type='SmoothL1Loss',
                beta=1.0,
                loss_weight=1.0
            )
        )
    ),
    train_cfg=dict(
        rpn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.7,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                match_low_quality=True,
                ignore_iof_thr=-1
            ),
            sampler=dict(
                type='RandomSampler',
                num=256,
                pos_fraction=0.5,
                neg_pos_ub=-1,
                add_gt_as_proposals=False
            ),
            allowed_border=-1,
            pos_weight=-1,
            debug=False
        ),
        rpn_proposal=dict(
            nms_pre=2000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0
        ),
        rcnn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.5,
                neg_iou_thr=0.5,
                min_pos_iou=0.5,
                match_low_quality=False,
                ignore_iof_thr=-1
            ),
            sampler=dict(
                type='RandomSampler',
                num=512,
                pos_fraction=0.25,
                neg_pos_ub=-1,
                add_gt_as_proposals=True
            ),
            pos_weight=-1,
            debug=False
        )
    ),
    test_cfg=dict(
        rpn=dict(
            nms_pre=1000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0
        ),
        rcnn=dict(
            score_thr=0.05,
            nms=dict(type='nms', iou_threshold=0.5),
            max_per_img=100
        )
    )
)

# Dataset configuration
# 数据集配置
dataset_type = 'COCODataset'
data_root = 'main_models_train/data/processed_dataset/'
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53],
    std=[58.395, 57.12, 57.375],
    to_rgb=True
)

# Enhanced training pipeline with augmentations
train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(
        type='Resize',
        img_scale=[(1280, 1280), (800, 800)],  # Multi-scale training
        multiscale_mode='range',
        keep_ratio=True
    ),
    dict(
        type='AutoAugment',
        policies=[
            [
                dict(type='RandomRotate', prob=0.5, level=5),
                dict(type='BrightnessTransform', level=5)
            ],
            [
                dict(type='RandomContrast', prob=0.5),
                dict(type='Blur', prob=0.3)
            ]
        ]
    ),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels'])
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1280, 1280),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img'])
        ]
    )
]

data = dict(
    samples_per_gpu=2,
    workers_per_gpu=2,
    train=dict(
        type=dataset_type,
        ann_file=data_root + 'train/annotations/_annotations.coco.json',
        img_prefix=data_root + 'train/images',
        pipeline=train_pipeline
    ),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'val/annotations/_annotations.coco.json',
        img_prefix=data_root + 'val/images',
        pipeline=test_pipeline
    ),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'test/annotations/_annotations.coco.json',
        img_prefix=data_root + 'test/images',
        pipeline=test_pipeline
    )
)

# Enhanced training configuration
# 增强的训练配置
optimizer = dict(
    type='AdamW',  # Switch to AdamW
    lr=0.0001,
    betas=(0.9, 0.999),
    weight_decay=0.05,
    paramwise_cfg=dict(
        custom_keys={
            'absolute_pos_embed': dict(decay_mult=0.),
            'relative_position_bias_table': dict(decay_mult=0.),
            'norm': dict(decay_mult=0.)
        }
    )
)
optimizer_config = dict(
    grad_clip=dict(max_norm=35, norm_type=2),
    type='Fp16OptimizerHook',  # Enable mixed precision
    loss_scale=dict(init_scale=512)
)
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=500,
    warmup_ratio=0.001,
    step=[8, 11]
)
runner = dict(type='EpochBasedRunner', max_epochs=12)

# Enhanced runtime configuration
# 增强的运行时配置
checkpoint_config = dict(
    interval=1,
    max_keep_ckpts=3,  # Only keep latest 3 checkpoints
    save_optimizer=True,
    save_last=True  # Always save last checkpoint for resuming
)
log_config = dict(
    interval=50,
    hooks=[
        dict(type='TextLoggerHook'),
        dict(type='TensorboardLoggerHook'),
        dict(type='MMDetWandbHook',
             init_kwargs={
                 'project': 'colony-detection',
                 'group': 'faster-rcnn',
             },
             interval=50,
             log_checkpoint=True,
             log_checkpoint_metadata=True,
             num_eval_images=100)
    ]
)
custom_hooks = [dict(type='NumClassCheckHook')]
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]
# Performance optimization
# 性能优化
opencv_num_threads = 0
mp_start_method = 'fork'
seed = 42
deterministic = True  # Ensure reproducibility
cudnn_benchmark = True  # Enable cudnn benchmark for faster training

# Auto-scaling config
# 自动缩放配置
auto_scale_lr = dict(enable=True, base_batch_size=16)

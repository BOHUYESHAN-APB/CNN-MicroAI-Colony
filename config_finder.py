import os
import glob
import shutil

def find_configs(base_dir=None):
    """查找项目中所有可能的配置文件"""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"在 {base_dir} 查找配置文件...")
    config_files = []
    
    # 搜索所有可能的Python配置文件
    for root, _, _ in os.walk(base_dir):
        configs = glob.glob(os.path.join(root, "**/*.py"), recursive=True)
        for config in configs:
            # 只保留可能是配置文件的路径
            if "config" in config.lower() or "_rcnn" in config.lower():
                config_files.append(config)
    
    return config_files

def create_default_faster_rcnn_config(target_path="/workspace/configs/faster_rcnn_colony.py"):
    """创建默认的Faster RCNN配置文件"""
    # 确保目录存在
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # 默认配置内容
    config_content = """
# model settings
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
        init_cfg=dict(type='Pretrained', checkpoint='torchvision://resnet50')),
    neck=dict(
        type='FPN',
        in_channels=[256, 512, 1024, 2048],
        out_channels=256,
        num_outs=5),
    rpn_head=dict(
        type='RPNHead',
        in_channels=256,
        feat_channels=256,
        anchor_generator=dict(
            type='AnchorGenerator',
            scales=[8],
            ratios=[0.5, 1.0, 2.0],
            strides=[4, 8, 16, 32, 64]),
        bbox_coder=dict(
            type='DeltaXYWHBBoxCoder',
            target_means=[.0, .0, .0, .0],
            target_stds=[1.0, 1.0, 1.0, 1.0]),
        loss_cls=dict(
            type='CrossEntropyLoss', use_sigmoid=True, loss_weight=1.0),
        loss_bbox=dict(type='L1Loss', loss_weight=1.0)),
    roi_head=dict(
        type='StandardRoIHead',
        bbox_roi_extractor=dict(
            type='SingleRoIExtractor',
            roi_layer=dict(type='RoIAlign', output_size=7, sampling_ratio=0),
            out_channels=256,
            featmap_strides=[4, 8, 16, 32]),
        bbox_head=dict(
            type='Shared2FCBBoxHead',
            in_channels=256,
            fc_out_channels=1024,
            roi_feat_size=7,
            num_classes=1,  # 假设只有一个类别：菌落
            bbox_coder=dict(
                type='DeltaXYWHBBoxCoder',
                target_means=[0., 0., 0., 0.],
                target_stds=[0.1, 0.1, 0.2, 0.2]),
            reg_class_agnostic=False,
            loss_cls=dict(
                type='CrossEntropyLoss', use_sigmoid=False, loss_weight=1.0),
            loss_bbox=dict(type='L1Loss', loss_weight=1.0))),
    # 模型训练和测试参数
    train_cfg=dict(
        rpn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.7,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                match_low_quality=True,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=256,
                pos_fraction=0.5,
                neg_pos_ub=-1,
                add_gt_as_proposals=False),
            allowed_border=-1,
            pos_weight=-1,
            debug=False),
        rpn_proposal=dict(
            nms_pre=2000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                pos_iou_thr=0.5,
                neg_iou_thr=0.5,
                min_pos_iou=0.5,
                match_low_quality=False,
                ignore_iof_thr=-1),
            sampler=dict(
                type='RandomSampler',
                num=512,
                pos_fraction=0.25,
                neg_pos_ub=-1,
                add_gt_as_proposals=True),
            pos_weight=-1,
            debug=False)),
    test_cfg=dict(
        rpn=dict(
            nms_pre=1000,
            max_per_img=1000,
            nms=dict(type='nms', iou_threshold=0.7),
            min_bbox_size=0),
        rcnn=dict(
            score_thr=0.05,
            nms=dict(type='nms', iou_threshold=0.5),
            max_per_img=100)))

# 数据集设置
dataset_type = 'CocoDataset'
data_root = 'data/coco/'  # 请修改为你的实际数据路径
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(1333, 800), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1333, 800),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]

data = dict(
    samples_per_gpu=2,
    workers_per_gpu=2,
    train=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_train2017.json',  # 请修改为你的标注文件
        img_prefix=data_root + 'train2017/',  # 请修改为你的图像目录
        pipeline=train_pipeline),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_val2017.json',  # 请修改为你的标注文件
        img_prefix=data_root + 'val2017/',  # 请修改为你的图像目录
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'annotations/instances_val2017.json',  # 请修改为你的标注文件
        img_prefix=data_root + 'val2017/',  # 请修改为你的图像目录
        pipeline=test_pipeline))

# 优化器设置
optimizer = dict(type='SGD', lr=0.02, momentum=0.9, weight_decay=0.0001)
optimizer_config = dict(grad_clip=None)

# 学习率设置
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=500,
    warmup_ratio=0.001,
    step=[8, 11])

# 总共跑12轮
runner = dict(type='EpochBasedRunner', max_epochs=12)

# 评估设置
evaluation = dict(interval=1, metric='bbox')

# 检查点和日志设置
checkpoint_config = dict(interval=1)
log_config = dict(
    interval=50,
    hooks=[
        dict(type='TextLoggerHook'),
    ])

# 其他设置
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None  # 可以设置预训练模型路径
resume_from = None
workflow = [('train', 1)]
"""

    with open(target_path, 'w') as f:
        f.write(config_content)
    
    print(f"已创建默认配置文件: {target_path}")
    return target_path

def check_for_configs():
    """检查并处理配置文件"""
    # 首先确认配置文件是否存在
    target_config = "/workspace/configs/faster_rcnn_colony.py"
    
    if os.path.exists(target_config):
        print(f"配置文件已存在: {target_config}")
        return target_config
    
    # 寻找可能的配置文件
    print("未找到默认配置文件，正在搜索替代配置...")
    configs = find_configs()
    
    if configs:
        print("找到以下可能的配置文件:")
        for i, config in enumerate(configs):
            print(f"{i+1}. {config}")
        
        # 询问用户是否使用找到的配置文件或创建新文件
        print("\n选项:")
        print("1. 使用上述找到的配置文件之一")
        print("2. 创建默认配置文件")
        
        choice = input("请选择 (1/2): ")
        
        if choice == "1":
            try:
                idx = int(input(f"请输入文件编号 (1-{len(configs)}): ")) - 1
                if 0 <= idx < len(configs):
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(target_config), exist_ok=True)
                    # 复制选定的配置文件
                    shutil.copy(configs[idx], target_config)
                    print(f"已复制 {configs[idx]} 到 {target_config}")
                    return target_config
            except (ValueError, IndexError):
                print("无效的选择，将创建默认配置文件")
    
    # 如果没有找到配置文件或用户选择创建新文件
    return create_default_faster_rcnn_config(target_config)

if __name__ == "__main__":
    check_for_configs()

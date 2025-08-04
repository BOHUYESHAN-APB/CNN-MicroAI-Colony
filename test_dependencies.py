try:
    print("开始检查依赖库...")
    
    # 尝试导入 torch
    try:
        import torch
        print("torch 已安装")
    except ImportError:
        print("torch 未安装")
    
    # 尝试导入 yaml
    try:
        import yaml
        print("yaml 已安装")
    except ImportError:
        print("yaml 未安装")
    
    # 尝试导入 ultralytics
    try:
        import ultralytics
        print("ultralytics 已安装")
    except ImportError:
        print("ultralytics 未安装")
    
    # 尝试导入 torchvision
    try:
        import torchvision
        print("torchvision 已安装")
    except ImportError:
        print("torchvision 未安装")
    
    print("依赖检查完成")
except Exception as e:
    import traceback
    print(f"执行过程中出现错误: {e}")
    traceback.print_exc()
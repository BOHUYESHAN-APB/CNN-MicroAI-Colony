import os
import re
import shutil
import glob

def fix_config_file(config_path="/workspace/configs/faster_rcnn_colony.py"):
    """修复配置文件中的数据集注册名和路径问题"""
    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        return False
    
    # 读取配置文件
    with open(config_path, 'r') as f:
        content = f.read()
    
    # 修复数据集类型名称的大小写
    modified_content = content
    if 'COCODataset' in modified_content:
        print("修复数据集名称: COCODataset -> CocoDataset")
        modified_content = modified_content.replace('COCODataset', 'CocoDataset')
    
    # 检查数据目录是否存在，如果不存在，尝试找到实际路径
    data_root_match = re.search(r"data_root\s*=\s*['\"](.*?)['\"]", modified_content)
    if data_root_match:
        data_root = data_root_match.group(1)
        if not os.path.exists(data_root):
            print(f"数据路径不存在: {data_root}，尝试查找有效路径...")
            
            # 尝试在工作空间中查找可能的数据目录
            possible_data_dirs = []
            for root, dirs, _ in os.walk("/workspace"):
                for dir_name in dirs:
                    if "data" in dir_name.lower() or "dataset" in dir_name.lower() or "coco" in dir_name.lower():
                        full_path = os.path.join(root, dir_name)
                        possible_data_dirs.append(full_path)
            
            if possible_data_dirs:
                print("找到可能的数据目录:")
                for i, path in enumerate(possible_data_dirs):
                    print(f"{i+1}. {path}")
                
                print("\n请选择数据目录并更新配置文件中的路径")
                print(f"您可以手动修改配置文件 {config_path} 中的 data_root 值")
                
                # 为了安全起见，我们不自动修改路径，而是建议用户手动选择
            else:
                print("未找到可能的数据目录，请手动配置数据路径")
    
    # 保存修改后的配置
    if content != modified_content:
        # 备份原始文件
        backup_path = f"{config_path}.bak"
        shutil.copy(config_path, backup_path)
        print(f"已备份原始配置文件到 {backup_path}")
        
        # 写入修改后的内容
        with open(config_path, 'w') as f:
            f.write(modified_content)
        print(f"已更新配置文件 {config_path}")
        return True
    else:
        print("配置文件无需修改")
        return False

def find_train_script():
    """查找训练脚本"""
    train_scripts = []
    
    # 在工作空间查找训练脚本
    for path in glob.glob("/workspace/**/*.py", recursive=True):
        filename = os.path.basename(path)
        if "train" in filename.lower():
            train_scripts.append(path)
    
    return train_scripts

def show_instructions(config_path="/workspace/configs/faster_rcnn_colony.py"):
    """显示如何修改训练脚本以指向正确的配置文件"""
    train_scripts = find_train_script()
    
    print("\n===== 使用说明 =====")
    print(f"1. 确保配置文件存在且配置正确: {config_path}")
    print("2. 修改训练脚本中的配置文件路径:")
    
    if train_scripts:
        print("\n找到可能的训练脚本:")
        for i, script in enumerate(train_scripts):
            print(f"   {i+1}. {script}")
        
        print("\n在训练脚本中，找到加载配置文件的代码行，修改为:")
        print(f"   config_file = '{config_path}'  # 或使用相对路径")
        print("   cfg = Config.fromfile(config_file)")
    else:
        print("未找到训练脚本，请手动确认训练脚本中使用了正确的配置文件路径")
    
    print("\n示例：如果您的训练脚本位于 /workspace/train.py，您可以这样运行:")
    print(f"python /workspace/train.py --config {config_path}")
    print("或者修改训练脚本中的配置文件路径")

if __name__ == "__main__":
    fix_config_file()
    show_instructions()

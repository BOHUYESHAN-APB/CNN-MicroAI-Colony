import sys
import os

print("Python 环境测试")
print(f"Python 版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print(f"命令行参数: {sys.argv}")

try:
    print("\n测试导入模块:")
    modules = ['torch', 'torchvision', 'yaml', 'ultralytics', 'mmdet', 'paddle']
    for module in modules:
        try:
            __import__(module)
            print(f"  - {module}: 成功")
        except ImportError as e:
            print(f"  - {module}: 失败 ({e})")
    
    print("\n测试文件操作:")
    test_file = "test_env_output.txt"
    with open(test_file, "w") as f:
        f.write("测试文件写入成功")
    print(f"  - 文件写入: 成功 ({test_file})")
    
    with open(test_file, "r") as f:
        content = f.read()
    print(f"  - 文件读取: 成功 ({content})")
    
    os.remove(test_file)
    print(f"  - 文件删除: 成功")
    
    print("\n测试目录操作:")
    print(f"  - 当前目录内容: {os.listdir('.')}")
    
    print("\n环境测试完成")
except Exception as e:
    import traceback
    print(f"测试过程中出现错误: {e}")
    traceback.print_exc()
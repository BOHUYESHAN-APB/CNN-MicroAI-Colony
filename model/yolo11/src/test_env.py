import os
import sys
print("Current directory:", os.getcwd())
print("Python path:", sys.path)
print("Environment path:", os.environ.get('PATH'))

try:
    print("Importing required modules...")
    import torch
    print("PyTorch version:", torch.__version__)
    import albumentations as A
    print("Albumentations version:", A.__version__)
    
    print("\nChecking config file...")
    if os.path.exists('config.yaml'):
        print("config.yaml found")
        with open('config.yaml', 'r') as f:
            print("Config contents:", f.read())
    else:
        print("config.yaml not found")
    
    print("\nTrying to import train module...")
    import train
    print("Successfully imported train")
    
    print("\nTrying to create trainer...")
    trainer = train.Trainer('config.yaml')
    print("Successfully created trainer")
    
except Exception as e:
    print(f"\nError occurred: {str(e)}")
    import traceback
    traceback.print_exc()

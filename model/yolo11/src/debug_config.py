import os
import sys
import yaml

def print_separator():
    print("=" * 80)

def main():
    try:
        print_separator()
        print("SYSTEM INFORMATION")
        print_separator()
        print(f"Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Absolute current directory: {os.path.abspath('.')}")
        print(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")
        
        print("\nDirectory contents:")
        for item in sorted(os.listdir('.')):
            print(f"  {item}")
            if os.path.isdir(item):
                for subitem in sorted(os.listdir(item)):
                    print(f"    {subitem}")

        print_separator()
        print("CONFIG LOADING")
        print_separator()
        
        current_dir = os.path.abspath('.')
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            print(f"Added {current_dir} to Python path")
        
        print("\nTrying to import utils.config...")
        from utils.config import Config
        print("Successfully imported Config")
        
        config_path = os.path.abspath('config.yaml')
        print(f"\nChecking if config file exists at {config_path}...")
        if os.path.exists(config_path):
            print("Config file found")
            
            print("\nTrying to read config file directly...")
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Raw content:\n{content}")
                raw_config = yaml.safe_load(content)
                print(f"Parsed config: {raw_config}")
            
            print("\nTrying to load config through Config class...")
            config = Config(config_path)
            print("Config loaded successfully")
            
            print("\nTrying to access config values...")
            print(f"model.num_classes: {config['model']['num_classes']}")
            print(f"model.image_size: {config['model']['image_size']}")
            print(f"data.train_path: {config['data']['train_path']}")
            print(f"training.device: {config['training']['device']}")
            
        else:
            print("Config file not found!")
            print("Looking for config.yaml in parent directories...")
            parent = os.path.dirname(current_dir)
            while parent and parent != os.path.dirname(parent):
                test_path = os.path.join(parent, 'config.yaml')
                if os.path.exists(test_path):
                    print(f"Found config file at: {test_path}")
                    break
                parent = os.path.dirname(parent)
            
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

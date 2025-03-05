import os
import sys
import shutil
import subprocess
from pathlib import Path
import PyInstaller.__main__
import argparse

def cleanup_build():
    """Clean up build artifacts"""
    print("Cleaning up previous build...")
    paths_to_remove = ['build', 'dist']
    for path in paths_to_remove:
        if os.path.exists(path):
            shutil.rmtree(path)
    spec_file = 'colony_counter.spec'
    if os.path.exists(spec_file):
        os.remove(spec_file)

def export_model(checkpoint_path, output_path):
    """Export PyTorch model to ONNX"""
    print("Exporting model to ONNX format...")
    from app.utils.export_onnx import export_to_onnx
    export_to_onnx(checkpoint_path, output_path)

def build_executable(debug=False):
    """Build executable using PyInstaller"""
    print("Building executable...")
    
    # Prepare additional files
    datas = [
        ('app/templates', 'templates'),
        ('app/config.yaml', 'config.yaml'),
        ('model.onnx', 'model.onnx')  # ONNX model file
    ]
    
    # Prepare PyInstaller arguments
    args = [
        'app/main.py',
        '--name=colony_counter',
        '--onefile',
        '--windowed',
        '--icon=app/resources/icon.ico',
    ]
    
    # Add data files
    for src, dst in datas:
        args.extend(['--add-data', f'{src}{os.pathsep}{dst}'])
    
    # Add debug options if requested
    if debug:
        args.append('--debug=all')
        args.append('--log-level=DEBUG')
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)

def main():
    parser = argparse.ArgumentParser(description='Build Colony Counter executable')
    parser.add_argument('--checkpoint', type=str, required=True,
                       help='Path to PyTorch checkpoint for ONNX export')
    parser.add_argument('--debug', action='store_true',
                       help='Build with debug information')
    parser.add_argument('--no-cleanup', action='store_true',
                       help='Skip cleanup of previous build artifacts')
    
    args = parser.parse_args()
    
    try:
        # Clean up previous build
        if not args.no_cleanup:
            cleanup_build()
        
        # Export model to ONNX
        export_model(args.checkpoint, 'model.onnx')
        
        # Build executable
        build_executable(debug=args.debug)
        
        print("\nBuild completed successfully!")
        print(f"Executable can be found in: {os.path.abspath('dist')}")
        
    except Exception as e:
        print(f"\nError during build: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()

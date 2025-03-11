#!/usr/bin/env python3
"""
MicroAI-Colony Application Runner
"""
import os
import sys

def setup_environment():
    """Setup application environment"""
    try:
        # Add project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            
        # Create required directories
        dirs = [
            "app/config/defaults",
            "app/resources/i18n/qm",
            "app/resources/i18n/ts",
            "app/resources/themes",
            "app/data/projects",
            "app/logs",
            "app/results"
        ]
        
        for d in dirs:
            os.makedirs(os.path.join(project_root, d), exist_ok=True)
            
        return True
        
    except Exception as e:
        print(f"Error setting up environment: {e}")
        return False

def check_dependencies():
    """Check required dependencies"""
    try:
        import PyQt6
        import numpy
        import cv2
        import matplotlib
        return True
        
    except ImportError as e:
        print("Missing required dependencies:")
        print("  pip install -r requirements.txt")
        return False

def main():
    """Application entry point"""
    try:
        # Setup environment
        if not setup_environment():
            return 1
            
        # Check dependencies
        if not check_dependencies():
            return 1
            
        # Import and run application
        from app.main import main
        return main()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

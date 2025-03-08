import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)

class PathManager:
    """Utility class for managing application paths and directories"""
    
    @staticmethod
    def get_app_dir() -> Path:
        """Get the application's root directory"""
        return Path(__file__).parent.parent

    @staticmethod
    def get_resource_dir() -> Path:
        """Get resources directory"""
        return PathManager.get_app_dir() / "resources"

    @staticmethod
    def get_log_dir() -> Path:
        """Get logs directory"""
        log_dir = PathManager.get_app_dir() / "logs"
        log_dir.mkdir(exist_ok=True)
        return log_dir

    @staticmethod
    def get_config_dir() -> Path:
        """Get configuration directory"""
        if os.name == "nt":  # Windows
            config_dir = Path(os.getenv("APPDATA")) / "Colony Detection"
        else:  # Linux/Mac
            config_dir = Path.home() / ".config" / "colony-detection"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @staticmethod
    def create_project_dir(project_name: str, base_path: Optional[str] = None) -> Path:
        """Create a new project directory with timestamp"""
        if not base_path:
            base_path = str(Path.home() / "Desktop" / "MicroAI_Detect")
            
        # Create base directory if it doesn't exist
        base_dir = Path(base_path)
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        project_dir = base_dir / f"{project_name}_{timestamp}"
        project_dir.mkdir(exist_ok=True)
        
        # Create standard subdirectories
        (project_dir / "images").mkdir(exist_ok=True)
        (project_dir / "results").mkdir(exist_ok=True)
        (project_dir / "exports").mkdir(exist_ok=True)
        (project_dir / "logs").mkdir(exist_ok=True)
        
        logger.info(f"Created project directory: {project_dir}")
        return project_dir

    @staticmethod
    def validate_project_dir(path: str) -> bool:
        """Check if directory is a valid project directory"""
        project_dir = Path(path)
        required_dirs = ["images", "results", "exports", "logs"]
        
        return (
            project_dir.is_dir() and
            all((project_dir / d).is_dir() for d in required_dirs)
        )

    @staticmethod
    def get_project_log_file(project_dir: Path) -> Path:
        """Get project-specific log file path"""
        log_dir = project_dir / "logs"
        timestamp = datetime.now().strftime("%Y%m%d")
        return log_dir / f"project_{timestamp}.log"

    @staticmethod
    def get_export_path(project_dir: Path, prefix: str, ext: str) -> Path:
        """Generate export file path with timestamp"""
        export_dir = project_dir / "exports"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return export_dir / f"{prefix}_{timestamp}.{ext}"

    @staticmethod
    def list_project_images(project_dir: Path) -> List[Path]:
        """List all images in project's image directory"""
        image_dir = project_dir / "images"
        image_extensions = [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
        
        images = []
        for ext in image_extensions:
            images.extend(image_dir.glob(f"*{ext}"))
            images.extend(image_dir.glob(f"*{ext.upper()}"))
            
        return sorted(images)

    @staticmethod
    def copy_to_project(project_dir: Path, file_paths: List[str], subdir: str = "images") -> List[Path]:
        """Copy files to project directory and return new paths"""
        dest_dir = project_dir / subdir
        new_paths = []
        
        for file_path in file_paths:
            src = Path(file_path)
            if src.exists():
                dest = dest_dir / src.name
                shutil.copy2(src, dest)
                new_paths.append(dest)
                logger.info(f"Copied {src} to {dest}")
            else:
                logger.warning(f"Source file not found: {src}")
                
        return new_paths

    @staticmethod
    def cleanup_project(project_dir: Path, keep_results: bool = True):
        """Clean up temporary files in project directory"""
        # Implementation depends on what needs to be cleaned up
        pass

def create_app_dirs():
    """Create all necessary application directories"""
    try:
        PathManager.get_resource_dir()
        PathManager.get_log_dir()
        PathManager.get_config_dir()
        logger.info("Application directories created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create application directories: {e}")
        return False

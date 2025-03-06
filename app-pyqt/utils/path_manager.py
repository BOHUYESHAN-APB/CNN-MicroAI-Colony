import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

class PathManager:
    """Manage application paths and directories"""
    
    def __init__(self, config):
        self.config = config
        self.app_name = "MicroAI Detect"
        self.active_project = None
        self.initialize_paths()
        
    def initialize_paths(self):
        """Initialize base directories"""
        # 默认使用桌面路径
        self.desktop_dir = Path.home() / "Desktop"
        self.base_dir = self.config.get('paths.base_dir')
        
        if not self.base_dir:
            self.base_dir = self.desktop_dir / self.app_name
            self.config.set('paths.base_dir', str(self.base_dir))
            self.config.save()
            
        self.base_dir = Path(self.base_dir)
        
    @property
    def has_active_project(self) -> bool:
        """Check if there is an active project"""
        return self.active_project is not None
        
    def create_project(self, name: str) -> Path:
        """Create new project directory structure"""
        project_dir = self.base_dir / name
        if project_dir.exists():
            suffix = 1
            while (self.base_dir / f"{name}_{suffix}").exists():
                suffix += 1
            project_dir = self.base_dir / f"{name}_{suffix}"
            
        try:
            # Create project structure
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "PIC").mkdir(exist_ok=True)
            (project_dir / "logs").mkdir(exist_ok=True)
            (project_dir / "results").mkdir(exist_ok=True)
            (project_dir / "results" / "single").mkdir(exist_ok=True)
            (project_dir / "results" / "batch").mkdir(exist_ok=True)
            
            # Set as active project
            self.active_project = project_dir
            self.config.set('project.current', str(project_dir))
            self.config.set('project.name', project_dir.name)
            self.config.save()
            
            logger.info(f"Created project: {name}")
            return project_dir
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
            
    def load_project(self, project_path: str) -> Path:
        """Load existing project"""
        project_dir = Path(project_path)
        if not project_dir.exists():
            raise FileNotFoundError(f"Project directory not found: {project_path}")
            
        # Verify project structure
        required_dirs = ["PIC", "logs", "results"]
        for dir_name in required_dirs:
            if not (project_dir / dir_name).exists():
                (project_dir / dir_name).mkdir(parents=True, exist_ok=True)
                
        # Set as active project
        self.active_project = project_dir
        self.config.set('project.current', str(project_dir))
        self.config.set('project.name', project_dir.name)
        self.config.save()
        
        return project_dir
        
    def import_images(self, image_paths: List[str]) -> List[Path]:
        """Import images to project PIC directory"""
        if not self.active_project:
            raise RuntimeError("No active project")
            
        pic_dir = self.active_project / "PIC"
        imported = []
        
        for path in image_paths:
            src = Path(path)
            if not src.exists():
                continue
                
            # Copy image to project
            dst = pic_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
                imported.append(dst)
                
        return imported
        
    def get_image_output_dir(self, image_path: str, timestamp: Optional[str] = None, 
                            batch_mode: bool = False) -> Path:
        """Get output directory for image results"""
        if not self.active_project:
            raise RuntimeError("No active project")
            
        # Use image name as subdirectory
        image_name = Path(image_path).stem
        
        # Create timestamp if not provided
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        # Determine base path based on mode
        if batch_mode:
            base_path = self.active_project / "results" / "batch" / timestamp
        else:
            base_path = self.active_project / "results" / "single" / image_name / timestamp
            
        # Create directories
        base_path.mkdir(parents=True, exist_ok=True)
        (base_path / "data").mkdir(exist_ok=True)
        (base_path / "plots").mkdir(exist_ok=True)
        
        return base_path
        
    def get_log_file(self) -> Path:
        """Get path for log file"""
        if not self.active_project:
            raise RuntimeError("No active project")
            
        logs_dir = self.active_project / "logs"
        timestamp = datetime.now().strftime("%Y%m%d")
        return logs_dir / f"log_{timestamp}.txt"
        
    def clear_project(self):
        """Clear current project"""
        self.active_project = None
        self.config.set('project.current', None)
        self.config.set('project.name', '')
        self.config.save()

    def get_default_export_formats(self) -> List[str]:
        """Get configured export formats"""
        formats = self.config.get('analysis.auto_export.formats', [])
        if not formats:
            formats = ['excel']  # Default format
        return formats

    def is_auto_export_enabled(self) -> bool:
        """Check if auto export is enabled"""
        return self.config.get('analysis.auto_export.enabled', True)

    def get_batch_output_name(self, timestamp: str) -> str:
        """Get batch analysis output name"""
        return f"batch_analysis_{timestamp}"

    def get_multi_image_output_dir(self, timestamp: Optional[str] = None) -> Path:
        """Get output directory for multi-image analysis"""
        if not self.active_project:
            raise RuntimeError("No active project")
            
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        output_dir = self.active_project / "results" / "batch" / f"multi_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

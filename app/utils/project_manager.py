"""
Project Manager
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..config import ConfigManager
from .path_manager import (
    get_projects_dir, create_project_dir, normalize_path,
    ensure_project_structure, is_valid_project_dir, get_project_images,
    clean_project_name, get_project_name
)

logger = logging.getLogger(__name__)

class ProjectManager:
    """Project manager singleton"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not ProjectManager._initialized:
            self.current_project = None
            self.config = ConfigManager()
            ProjectManager._initialized = True
            
    def create_project(self, name: str, path: Optional[str] = None) -> bool:
        """Create new project"""
        try:
            # Get project directory
            if path:
                base_dir = normalize_path(path)
            else:
                base_dir = get_projects_dir()
                
            # Create project directory with name
            project_dir = create_project_dir(base_dir, name)
            if not project_dir:
                logger.error("Failed to create project directory")
                return False
                
            # Set as current project
            self.current_project = project_dir
            
            logger.info(f"Created new project: {project_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return False
            
    def open_project(self, path: str) -> bool:
        """Open existing project"""
        try:
            project_dir = normalize_path(path)
            
            # Validate project directory
            if not is_valid_project_dir(project_dir):
                logger.error(f"Not a valid project directory: {project_dir}")
                return False
                
            # Ensure structure is complete
            if not ensure_project_structure(project_dir):
                logger.error(f"Failed to ensure project structure: {project_dir}")
                return False
                
            # Set as current project
            self.current_project = project_dir
            
            logger.info(f"Opened project: {project_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening project: {e}")
            return False
            
    def close_project(self) -> bool:
        """Close current project"""
        try:
            if self.current_project:
                self.save_project()
                self.current_project = None
            return True
        except Exception as e:
            logger.error(f"Error closing project: {e}")
            return False
            
    def save_project(self) -> bool:
        """Save current project metadata"""
        if not self.current_project:
            return False
            
        try:
            metadata = self.get_project_info()
            metadata["modified"] = str(Path(self.current_project).stat().st_mtime)
            
            metadata_file = os.path.join(self.current_project, "project.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            return False
            
    def get_project_info(self) -> Dict[str, Any]:
        """Get current project metadata and sync with actual files"""
        if not self.current_project:
            return {}
            
        try:
            metadata_file = os.path.join(self.current_project, "project.json")
            
            # Load or create metadata
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    "name": get_project_name(self.current_project),
                    "created": str(Path(self.current_project).stat().st_ctime),
                    "modified": str(Path(self.current_project).stat().st_mtime),
                    "images": [],
                    "results": []
                }
            
            # Sync with actual files
            img_dir = os.path.join(self.current_project, "images")
            if os.path.exists(img_dir):
                # Get actual files
                actual_images = set()
                for img in Path(img_dir).glob("*.*"):
                    if img.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"]:
                        actual_images.add(str(img))
                
                # Keep only existing images in metadata
                metadata["images"] = [
                    img for img in metadata["images"]
                    if os.path.exists(img["path"]) and img["path"] in actual_images
                ]
                
                # Add any new images not in metadata
                existing_paths = {img["path"] for img in metadata["images"]}
                for img_path in actual_images:
                    if img_path not in existing_paths:
                        metadata["images"].append({
                            "path": img_path,
                            "name": os.path.basename(img_path),
                            "added": str(Path(img_path).stat().st_ctime)
                        })
            
            # Save synced metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
                
            return metadata
        except Exception as e:
            logger.error(f"Error reading project metadata: {e}")
            return {}
            
    def get_project_path(self) -> Optional[str]:
        """Get current project path"""
        return self.current_project
        
    def add_image(self, image_path: str) -> bool:
        """Add image to project"""
        if not self.current_project:
            return False
            
        try:
            # Copy image to project directory
            dest_dir = os.path.join(self.current_project, "images")
            os.makedirs(dest_dir, exist_ok=True)
            
            # Use same name but cleaned
            base_name = clean_project_name(os.path.basename(image_path))
            dest_path = os.path.join(dest_dir, base_name)
            
            # Add suffix if exists
            counter = 1
            orig_path = dest_path
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(orig_path)
                dest_path = f"{name}_{counter}{ext}"
                counter += 1
                
            # Copy file
            from shutil import copy2
            copy2(image_path, dest_path)
            
            # Update metadata
            metadata = self.get_project_info()
            metadata["images"].append({
                "path": dest_path,
                "name": os.path.basename(dest_path),
                "added": str(Path(dest_path).stat().st_ctime)
            })
            
            # Save metadata
            metadata_file = os.path.join(self.current_project, "project.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            return False
            
    def get_images(self) -> List[Dict[str, str]]:
        """Get list of project images"""
        if not self.current_project:
            return []
            
        return get_project_images(self.current_project)
        
    def remove_image(self, image_path: str) -> bool:
        """Remove image from project"""
        if not self.current_project:
            return False
            
        try:
            # Delete image file
            if os.path.exists(image_path):
                os.remove(image_path)
                
            # Update metadata
            metadata = self.get_project_info()
            metadata["images"] = [img for img in metadata["images"] 
                                if img["path"] != image_path]
                                
            # Save metadata
            metadata_file = os.path.join(self.current_project, "project.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            logger.error(f"Error removing image: {e}")
            return False
            
    @classmethod
    def get_instance(cls) -> 'ProjectManager':
        """Get ProjectManager singleton instance"""
        if cls._instance is None:
            cls._instance = ProjectManager()
        return cls._instance

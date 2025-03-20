"""
Project management implementation
项目管理实现
"""
import os
import json
import shutil
import logging
from datetime import datetime
from PyQt6.QtCore import QDir

logger = logging.getLogger(__name__)

class ProjectManager:
    """Manager for project data and operations"""
    
    def __init__(self):
        self.current_project = None
        
    def create_project(self, path):
        """Create new project at path"""
        try:
            # Create directory structure
            os.makedirs(os.path.join(path, "images"), exist_ok=True)
            os.makedirs(os.path.join(path, "results"), exist_ok=True)
            
            # Create project file
            project_data = {
                "created": datetime.now().isoformat(),
                "name": os.path.basename(path),
                "images": [],
                "results": {}
            }
            
            project_file = os.path.join(path, "project.json")
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
                
            self.current_project = path
            logger.info(f"Created new project: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return False
            
    def open_project(self, path):
        """Open existing project"""
        try:
            # Convert path to native format
            path = QDir.toNativeSeparators(os.path.abspath(path))
            
            # Validate project
            if not self.validate_project(path):
                return False
                
            self.current_project = path
            logger.info(f"Opened project: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open project: {str(e)}")
            logger.debug(f"Original path: {path}", exc_info=True)
            return False
            
    def validate_project(self, path):
        """Validate project structure"""
        # Check directory structure
        if not os.path.isdir(path):
            return False
            
        if not os.path.isdir(os.path.join(path, "images")):
            return False
            
        if not os.path.isdir(os.path.join(path, "results")):
            return False
            
        # Check project file
        project_file = os.path.join(path, "project.json")
        if not os.path.isfile(project_file):
            return False
            
        # Validate project data
        try:
            with open(project_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            required_fields = ["created", "name", "images", "results"]
            if not all(field in data for field in required_fields):
                return False
                
        except Exception:
            return False
            
        return True
        
    def save_results(self, project_path, image_path, detections, stats):
        """Save detection results"""
        try:
            # Get relative image path
            rel_path = os.path.relpath(image_path, project_path)
            
            # Prepare result data
            result_data = {
                "image": rel_path,
                "timestamp": datetime.now().isoformat(),
                "detections": [
                    {
                        "center": det["center"],
                        "diameter": det["diameter"],
                        "confidence": det["confidence"],
                        "box": det["box"]
                    }
                    for det in detections
                ],
                "stats": stats
            }
            
            # Load project data
            project_file = os.path.join(project_path, "project.json")
            with open(project_file, "r", encoding="utf-8") as f:
                project_data = json.load(f)
                
            # Add/update image entry
            if rel_path not in project_data["images"]:
                project_data["images"].append(rel_path)
                
            # Add/update result
            project_data["results"][rel_path] = result_data
            
            # Save project data
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
                
            # Save annotated image
            result_image_path = os.path.join(
                project_path, 
                "results",
                os.path.splitext(os.path.basename(image_path))[0] + "_annotated.jpg"
            )
            
            # TODO: Save annotated image
            
            logger.info(f"Saved project results: {project_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return False
            
    def get_image_results(self, project_path, image_path):
        """Get results for specific image"""
        try:
            # Get relative image path 
            rel_path = os.path.relpath(image_path, project_path)
            
            # Load project data
            project_file = os.path.join(project_path, "project.json")
            with open(project_file, "r", encoding="utf-8") as f:
                project_data = json.load(f)
                
            # Return results if exists
            return project_data["results"].get(rel_path)
            
        except Exception as e:
            logger.error(f"Failed to get image results: {e}")
            return None
            
    def get_project_images(self, project_path):
        """Get list of images in project"""
        try:
            # Load project data
            project_file = os.path.join(project_path, "project.json")
            with open(project_file, "r", encoding="utf-8") as f:
                project_data = json.load(f)
                
            # Convert image paths to native format
            image_paths = []
            for img_path in project_data["images"]:
                abs_path = QDir.toNativeSeparators(os.path.join(project_path, img_path))
                image_paths.append(abs_path)
                
            return image_paths
            
        except Exception as e:
            logger.error(f"Failed to get project images: {e}")
            return []
            
    def backup_project(self, project_path, backup_path):
        """Create backup of project"""
        try:
            # Create backup folder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(
                backup_path,
                f"{os.path.basename(project_path)}_{timestamp}"
            )
            
            # Copy project
            shutil.copytree(project_path, backup_dir)
            
            logger.info(f"Created project backup: {backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup project: {e}")
            return False

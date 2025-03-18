"""
Project management utilities
项目管理工具
"""
import os
import json
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProjectManager:
    """Project management class"""
    
    def __init__(self):
        self.current_project = None
        
    def create_project(self, name, path):
        """
        Create new project
        
        Args:
            name (str): Project name
            path (str): Project directory path
        """
        try:
            # Use directory directly as project folder
            project_dir = path
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # Create project structure
            project = {
                "name": name,
                "path": project_dir,
                "images": [],
                "results": {}
            }
            
            # Save project data
            self.current_project = project
            self.save_project()
            logger.info(f"Created project: {name} at {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return False
            
    def open_project(self, path):
        """
        Open existing project
        
        Args:
            path (str): Project directory path
        """
        try:
            # Use directory as project
            project = {
                "name": os.path.basename(path),
                "path": path,
                "images": [],
                "results": {}
            }
            
            # Load existing images
            for file in os.listdir(path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    img_path = os.path.join(path, file)
                    project["images"].append(img_path)
                    
            # Load results if exist
            results_file = os.path.join(path, "results.json")
            if os.path.exists(results_file):
                with open(results_file, 'r', encoding='utf-8') as f:
                    project["results"] = json.load(f)
                    
            self.current_project = project
            logger.info(f"Opened project: {project['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening project: {str(e)}")
            return False
            
    def save_project(self):
        """Save current project results"""
        try:
            if not self.current_project:
                return False
                
            # Only save results data
            path = os.path.join(self.current_project["path"], "results.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.current_project["results"], f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved project results: {self.current_project['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")
            return False
            
    def close_project(self):
        """Close current project"""
        if self.current_project:
            self.save_project()  # Save before closing
            self.current_project = None
            return True
        return False
            
    def add_image(self, image_path):
        """
        Add image to project
        
        Args:
            image_path (str): Path to image file
        """
        try:
            if not self.current_project:
                return False
                
            # Copy image to project directory
            filename = os.path.basename(image_path)
            target_path = os.path.join(self.current_project["path"], filename)
            
            if target_path not in self.current_project["images"]:
                shutil.copy2(image_path, target_path)
                self.current_project["images"].append(target_path)
                logger.info(f"Added image: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding image: {str(e)}")
            return False
            
    def remove_image(self, image_path):
        """
        Remove image from project
        
        Args:
            image_path (str): Path to image file
        """
        try:
            if not self.current_project:
                return False
                
            if image_path in self.current_project["images"]:
                self.current_project["images"].remove(image_path)
                
                # Remove results if exist
                if image_path in self.current_project["results"]:
                    del self.current_project["results"][image_path]
                
                # Delete file
                if os.path.exists(image_path):
                    os.remove(image_path)
                    
                self.save_project()
                logger.info(f"Removed image: {os.path.basename(image_path)}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing image: {str(e)}")
            return False
            
    def get_images(self):
        """Get list of project images"""
        if not self.current_project:
            return []
        return self.current_project["images"]
            
    def save_results(self, image_path, results):
        """
        Save analysis results
        
        Args:
            image_path (str): Path to image file
            results (dict): Analysis results
        """
        try:
            if not self.current_project:
                return False
                
            self.current_project["results"][image_path] = results
            self.save_project()
            return True
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False
            
    def get_results(self, image_path):
        """
        Get analysis results for image
        
        Args:
            image_path (str): Path to image file
        """
        if not self.current_project:
            return None
        return self.current_project["results"].get(image_path)

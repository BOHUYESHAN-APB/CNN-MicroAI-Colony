"""
Project management utilities
项目管理工具
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

class ProjectManager:
    """Project management class"""
    
    def __init__(self, project_dir):
        """Initialize project manager
        
        Args:
            project_dir: Project directory path
        """
        self.project_dir = project_dir
        self.config = {
            'name': os.path.basename(project_dir),
            'images_dir': os.path.join(project_dir, 'images'),
            'results_dir': os.path.join(project_dir, 'results')
        }
        
        # Create project structure
        self._init_project_structure()
        
    def _init_project_structure(self):
        """Initialize project directory structure"""
        try:
            # Create directories
            for dir_path in [self.config['images_dir'], 
                           self.config['results_dir']]:
                os.makedirs(dir_path, exist_ok=True)
                
            # Create project config file
            config_file = os.path.join(self.project_dir, 'project.json')
            if not os.path.exists(config_file):
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error initializing project structure: {str(e)}")
            raise
            
    def get_image_files(self):
        """Get list of image files in project
        
        Returns:
            List of image file paths
        """
        try:
            image_dir = self.config['images_dir']
            if not os.path.exists(image_dir):
                return []
                
            # Get all image files
            extensions = ('.jpg', '.jpeg', '.png', '.bmp')
            image_files = []
            
            for file in os.listdir(image_dir):
                if file.lower().endswith(extensions):
                    image_files.append(os.path.join(image_dir, file))
                    
            return sorted(image_files)
            
        except Exception as e:
            logger.error(f"Error getting image files: {str(e)}")
            return []
            
    def save_results(self, image_path, results):
        """Save detection results
        
        Args:
            image_path: Path to source image
            results: Detection results
        """
        try:
            # Create results filename
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            results_file = os.path.join(
                self.config['results_dir'],
                f"{base_name}_results.json"
            )
            
            # Save results
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            raise

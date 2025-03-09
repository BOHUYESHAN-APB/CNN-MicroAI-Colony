"""
Path Manager
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# [Previous functions remain unchanged until get_project_images]

def get_project_images(project_dir: str) -> List[Dict[str, str]]:
    """Get list of images in a project
    Returns list of dictionaries with image info"""
    try:
        # Check project validity
        if not is_valid_project_dir(project_dir):
            logger.error(f"Not a valid project directory: {project_dir}")
            return []
            
        # Read project metadata
        metadata_file = os.path.join(project_dir, "project.json")
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        # Get images from metadata
        images = metadata.get("images", [])
        
        # Validate each image exists
        valid_images = []
        for img in images:
            if os.path.exists(img["path"]):
                valid_images.append(img)
            else:
                logger.warning(f"Image file not found: {img['path']}")
                
        return valid_images
        
    except Exception as e:
        logger.error(f"Error getting project images: {e}")
        return []

def get_app_dir() -> str:
    """Get application data directory"""
    if os.name == 'nt':  # Windows
        app_dir = os.path.join(os.environ['APPDATA'], "MicroAI-Colony")
    else:  # Linux/Mac
        app_dir = os.path.join(
            os.path.expanduser('~'),
            '.microai-colony'
        )
    return app_dir

def get_config_dir() -> str:
    """Get configuration directory"""
    return os.path.join(get_app_dir(), "config")

def get_logs_dir() -> str:
    """Get logs directory"""
    return os.path.join(get_app_dir(), "logs")

def get_data_dir() -> str:
    """Get data directory"""
    return os.path.join(get_app_dir(), "data")

def get_projects_dir() -> str:
    """Get projects directory"""
    return os.path.join(get_data_dir(), "projects")

def list_project_directories() -> List[Tuple[str, str]]:
    """List all project directories
    Returns list of tuples (path, name)"""
    try:
        projects_dir = get_projects_dir()
        if not os.path.exists(projects_dir):
            return []
            
        projects = []
        for item in os.listdir(projects_dir):
            path = os.path.join(projects_dir, item)
            if not is_valid_project_dir(path):
                continue
                
            # Read project name from metadata
            try:
                metadata_file = os.path.join(path, "project.json")
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                name = metadata.get("name", item)
            except:
                name = item
                
            projects.append((path, name))
            
        # Sort by name
        return sorted(projects, key=lambda x: x[1].lower())
        
    except Exception as e:
        logger.error(f"Error listing project directories: {e}")
        return []

def get_default_project_path() -> str:
    """Get default project path"""
    base_dir = get_projects_dir()
    
    # Find next available numbered directory
    counter = 1
    while True:
        project_dir = os.path.join(base_dir, str(counter))
        if not os.path.exists(project_dir):
            break
        counter += 1
        
    return project_dir

def get_resources_dir() -> str:
    """Get resources directory"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resources"
    )

def get_themes_dir() -> str:
    """Get themes directory"""
    return os.path.join(get_resources_dir(), "themes")

def get_i18n_dir() -> str:
    """Get internationalization directory"""
    return os.path.join(get_resources_dir(), "i18n")

def create_app_directories() -> bool:
    """Create application directories if they don't exist"""
    try:
        # Create required directories
        dirs = [
            get_app_dir(),
            get_config_dir(),
            get_logs_dir(),
            get_data_dir(),
            get_projects_dir()
        ]
        
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")
                
        return True
        
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def ensure_project_structure(path: str) -> bool:
    """Ensure project directory has required structure"""
    try:
        # Create project subdirectories
        subdirs = ["images", "results"]
        for subdir in subdirs:
            dir_path = os.path.join(path, subdir)
            os.makedirs(dir_path, exist_ok=True)
            
        # Create or update project metadata
        metadata_file = os.path.join(path, "project.json")
        if not os.path.exists(metadata_file):
            metadata = {
                "name": get_project_name(path),
                "created": str(Path(path).stat().st_ctime),
                "modified": str(Path(path).stat().st_mtime),
                "images": [],
                "results": []
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
                
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring project structure: {e}")
        return False
        
def normalize_path(path: str) -> str:
    """Normalize file path"""
    return str(Path(path).resolve())

def clean_filename(name: str) -> str:
    """Clean filename to be safe for all platforms"""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Ensure name isn't empty or just dots
    if not name or all(c == '.' for c in name):
        name = '_'
    return name

def clean_project_name(name: str) -> str:
    """Clean project name for use in paths and files"""
    # First clean as filename
    name = clean_filename(name)
    # Remove additional unwanted characters
    name = re.sub(r'[^\w\-.]', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Replace multiple underscores with single
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Ensure valid length (1-64 chars)
    if len(name) > 64:
        name = name[:64]
    if not name:
        name = 'project'
    return name

def create_project_dir(base_dir: str, name: Optional[str] = None) -> str:
    """Create a new project directory"""
    try:
        if name:
            # Use cleaned name as directory
            project_name = clean_project_name(name)
            project_dir = os.path.join(base_dir, project_name)
            
            # Add number suffix if exists
            counter = 1
            orig_dir = project_dir
            while os.path.exists(project_dir):
                project_dir = f"{orig_dir}_{counter}"
                counter += 1
        else:
            # Use incrementing number
            counter = 1
            while True:
                project_dir = os.path.join(base_dir, str(counter))
                if not os.path.exists(project_dir):
                    break
                counter += 1
                
        # Create project directory and structure
        os.makedirs(project_dir)
        ensure_project_structure(project_dir)
        
        return project_dir
        
    except Exception as e:
        logger.error(f"Error creating project directory: {e}")
        return ""
        
def get_subdirs(path: str) -> List[str]:
    """Get list of subdirectories"""
    try:
        return [d for d in os.listdir(path) 
                if os.path.isdir(os.path.join(path, d))]
    except Exception as e:
        logger.error(f"Error getting subdirectories: {e}")
        return []

def get_project_name(path: str) -> str:
    """Get project name from path"""
    try:
        return os.path.basename(path)
    except Exception as e:
        logger.error(f"Error getting project name: {e}")
        return ""

def ensure_dir_exists(path: str) -> bool:
    """Ensure directory exists, create if necessary"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False

def is_valid_project_dir(path: str) -> bool:
    """Check if directory is a valid project directory"""
    try:
        # Check basic requirements
        if not os.path.isdir(path):
            return False
            
        # Check project metadata
        metadata_file = os.path.join(path, "project.json")
        if not os.path.exists(metadata_file):
            return False
            
        # Check required subdirectories
        for subdir in ["images", "results"]:
            if not os.path.isdir(os.path.join(path, subdir)):
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error checking project directory: {e}")
        return False

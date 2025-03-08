import logging
from pathlib import Path

class ProjectManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing ProjectManager")

    def create_project(self, project_path: Path):
        self.logger.info(f"Creating project at {project_path}")
        try:
            project_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create project: {e}")
            return False

    def load_project(self, project_path: Path):
        self.logger.info(f"Loading project from {project_path}")
        try:
            if project_path.exists() and project_path.is_dir():
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to load project: {e}")
            return False
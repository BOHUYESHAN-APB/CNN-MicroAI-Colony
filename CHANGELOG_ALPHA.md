# Changelog (Alpha)

## [1.0.0] - 2025-03-06

### Added
- **New Application Structure (app/)**:
  - Created a new directory structure for the modern PySide6-based application.
  - Initialized basic project files: `__init__.py`, `main.py`, `config/defaults.yaml`.
  - Set up core modules: `gui`, `models`, `resources`, `templates`, `utils`.
  - Integrated PyOneDark theme for a modern UI.
- **GUI Components**:
  - Created basic GUI structure in `app/gui/__init__.py`.
  - Added initial theme loading functionality.
  - Implemented basic window setup in `app/main.py`.
- **Configuration System**:
  - Created a basic configuration system with default settings in `app/config/defaults/defaults.yaml`.
- **Documentation Updates**:
  - Updated `README.md` to reflect the new application structure and versioning.
  - Added a new section for the "app" version in `README.md`.
  - Updated `docs/guides/USER_GUIDE.md` with initial usage instructions for the new version.
  - Updated `docs/guides/DATASET_CN.md` and `docs/guides/DATASET.md` to include information about the new version.
  - Updated `ALGORITHM_NOTES_CN.md` and `ALGORITHM_NOTES.md` to reflect the new architecture.

### Changed
- **Project Structure**:
  - Reorganized project to include a new `app` directory for the modern version.
  - Updated existing `app-pyqt` and `app-pyside6` directories to clarify their roles.
- **Documentation**:
  - Updated various documentation files to reflect the new project structure and features.

### Fixed
- Addressed several issues in `app_pyside6/gui/result_viewer.py`:
    - Fixed chart duplication and resource cleanup problems.
    - Improved error handling and logging.
    - Refactored code for better maintainability.
    - Added type hints for improved code clarity.

## [0.x.x] - Previous Versions
- Details of previous versions (app-pyqt and app-pyside6) can be found in their respective changelogs (if available).

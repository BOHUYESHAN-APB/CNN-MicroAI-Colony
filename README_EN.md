# Colony Detection and Analysis System

## Version Information

The project currently includes three versions:

### PyQt5 Version (app-pyqt/)
- Legacy version
- For research and learning purposes only
- Developed based on the PyQt5 framework

### PySide6 Version (app_pyside6/)
- Transition version
- Migrating to the PySide6 framework
- Maintaining basic functionality

### New Version (app/)
- Latest development version
- Based on PySide6 and PyOneDark theme
- Modern UI design
- Optimized user experience
- Improved performance and stability

## New Version Features
- Brand new dark-themed interface
- Smooth animations
- Better high DPI support
- Optimized performance and memory usage
- Modular code structure
- Complete type hints
- Comprehensive error handling

## Directory Structure
```
CNN-/
├── app/                # New version (in development)
│   ├── config/        # Configuration files
│   ├── database/      # Database management
│   ├── font/         # Font resources
│   ├── gui/          # Graphical interface
│   ├── models/       # Model definitions
│   ├── resources/    # Resource files
│   │   ├── i18n/    # Internationalization files
│   │   └── themes/  # Theme files
│   ├── templates/    # Report templates
│   └── utils/       # Utility functions
├── app_pyside6/      # Transition version
├── app-pyqt/         # Old version
├── docs/            # Documentation
└── src/            # Shared source code
```

## Tech Stack
- **GUI Framework**: PySide6 6.5+
- **Theme**: PyOneDark style
- **Deep Learning**: PyTorch 2.0+
- **Image Processing**: OpenCV 4.8+
- **Data Processing**: NumPy, Pandas
- **Visualization**: Matplotlib
- **Type Checking**: mypy
- **Code Quality**: pylint, black
- **Testing Framework**: pytest

## New Version Installation
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
```

## Development Notes
- Use Python 3.9+
- Follow PEP 8 coding style
- Use type annotations
- Write unit tests
- Keep documentation updated

## Licensing
Same as before, maintain the dual licensing model:
- Non-commercial use: AGPL v3
- Commercial use: Proprietary license

## Contribution Guide
1. Clone the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Contact
- Issue Tracking: GitHub Issues
- Feature Suggestions: Discussions
- Security Issues: Contact the maintainer directly

## Changelog
See CHANGELOG.md

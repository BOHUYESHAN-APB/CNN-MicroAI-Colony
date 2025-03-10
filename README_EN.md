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
- **Image Processing**: OpenCV 4.8+, incorporating Canny edge detection and Watershed algorithm in preprocessing for enhanced colony analysis.
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

## Performance Metrics

To track the impact of algorithm modifications, we've recorded performance changes after each significant update. The table below summarizes the error rates on the same set of test images used in the `test_model.py` script, across different algorithm versions.

| Image Name                  | Initial Error Rate (%) | Canny & Watershed Error Rate (%) | Canny & Watershed + GaussianBlur Error Rate (%) |
|---------------------------|-------------------------|------------------------------------|----------------------------------------------------|
| 2021041310020608608.jpg   | 0.9                     | 12.1                               | 0.9                                                |
| 2121.jpg                  | 2.5                     | 12.5                               | 2.5                                                |
| OIP-C.jpg                 | 27.3                    | 26.1                               | 27.3                                               |
| R-C.jpg                   | 56.4                    | 56.4                               | 52.1                                               |
| t019872959c62f44875.jpg   | 18.1                    | 22.3                               | 18.1                                               |
| **Average Error Rate**      | **21.0**                | **25.9**                               | **20.2**                                           |

**Note:** The table above is updated with error rates from different stages to clearly show the impact of each algorithm modification on performance. The "Canny & Watershed + GaussianBlur Error Rate" column reflects the performance metrics of the current latest model. Future performance metrics after algorithm optimizations will also be updated here.

As indicated in the table, the integration of Canny and Watershed algorithms initially led to a slight increase in the average error rate. However, with the GaussianBlur optimization of Canny and Watershed, the performance has returned to the initial level, with the average error rate decreasing to 20.2%. Furthermore, the error rate for R-C.jpg has improved from 56.4% to 52.1%, indicating a slight overall performance enhancement. We are committed to continuing the optimization of preprocessing and model parameters to further improve the overall performance from the current baseline.

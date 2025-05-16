# Development Guide

## Project Overview

This project consists of two main modules:
1. Colony counting system
2. Inhibition zone detection system

## Architecture

### Core Components

```
core/
├── detector.py      # Detection algorithms
├── models.py        # Data models
└── processor.py     # Image processing
```

### GUI Components

```
gui/
├── main_window.py   # Main window
├── image_view.py    # Image viewer
└── report_view.py   # Report display
```

### Utility Components

```
utils/
├── config.py        # Configuration management
└── i18n.py         # Internationalization
```

## Implementation Details

### Detection Algorithm

The inhibition zone detection uses a multi-stage approach:

1. Petri Dish Detection
```python
def detect_petri_dishes(image: np.ndarray) -> List[PetriDish]:
    # Pre-processing
    - Gaussian blur (kernel_size=9, sigma=2)
    # HoughCircles detection
    - Parameters: dp=1, minDist=400, param1=50, param2=35
    - Size limits based on image dimensions
```

2. Colony Detection
```python
def detect_colonies_in_dish(image: np.ndarray, dish: PetriDish) -> List[Colony]:
    # Three complementary methods:
    1. HSV color space analysis
    2. Adaptive thresholding
    3. Gradient-based detection
```

3. Inhibition Zone Analysis
```python
def detect_inhibition_zone(gray_image: np.ndarray, colony: Colony, dish: PetriDish):
    # Primary zone detection
    - Threshold range: 35-180
    - Area ratio validation: >0.8x filter paper area
    
    # Secondary zone detection
    - Threshold range: 65-160
    - Area ratio validation: >0.6x filter paper area
    
    # Overlap analysis
    - Morphological processing
    - Circularity validation (>0.5)
    - Minimum area filtering (50px²)
```

### User Interface

The GUI is implemented using PySide6 with a three-panel layout:

1. Resource Explorer
```python
class ResourceExplorer(QTreeView):
    # File system model integration
    # Directory navigation
    # File filtering
```

2. Image Viewer
```python
class ImageViewer(QWidget):
    # Image display and scaling
    # Annotation support
    # Interactive measurements
```

3. Report Panel
```python
class ReportView(QWidget):
    # Result visualization
    # Data statistics
    # Report generation
```

### Data Models

Core data structures:

1. PetriDish
```python
@dataclass
class PetriDish:
    center: Tuple[int, int]
    radius: int
    colonies: List[Colony]
    diameter_mm: float = 90.0
```

2. Colony
```python
@dataclass
class Colony:
    center: Tuple[int, int]
    radius: int
    contour: np.ndarray
    primary_inhibition_zone: Optional[Tuple[int, int, int]] = None
    secondary_inhibition_zone: Optional[Tuple[int, int, int]] = None
    overlap_zones: List[Tuple[int, int, int]] = field(default_factory=list)
```

## Development Setup

1. Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

2. Development Tools
```bash
# Code formatting
black .

# Linting
pylint opencv-circle-detection

# Type checking
mypy opencv-circle-detection
```

3. Testing
```bash
# Run unit tests
python -m unittest discover tests

# Generate test images
python create_test_image.py
```

## Code Style Guidelines

1. Python Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write docstrings for all public methods
- Keep methods focused and concise

2. Documentation
- Update README.md for major changes
- Document new features in guides
- Keep API documentation current

3. Git Workflow
- Create feature branches
- Write clear commit messages
- Submit pull requests for review

## Contributing

1. Development Process
- Fork the repository
- Create a feature branch
- Implement changes
- Write tests
- Submit pull request

2. Code Review
- All changes require review
- Tests must pass
- Documentation must be updated

3. Release Process
- Version bump
- Update changelog
- Create release notes
- Tag release

## Troubleshooting

Common development issues and solutions:

1. Import Issues
```python
# Add project root to PYTHONPATH
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
```

2. GUI Issues
```python
# Enable Qt debug output
QT_DEBUG=1 python main.py
```

3. Performance Issues
```python
# Profile code
python -m cProfile -o output.prof main.py
```

## Contact

- Technical Questions: GitHub Issues
- Code Reviews: Pull Requests
- Documentation: Wiki

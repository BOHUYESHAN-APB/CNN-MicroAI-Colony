# Colony Detection Analysis System

## Project Overview
A deep learning-based microbial colony detection and counting system that supports various culture media types and imaging conditions, providing accurate colony counting and analysis functionality.

## Directory Structure
```
CNN-/
├── app/                    # Application main directory
│   ├── config/            # Configuration files
│   ├── database/          # Database management
│   ├── font/             # Font resources
│   ├── gui/              # Graphical interface
│   ├── models/           # Model definitions
│   ├── resources/        # Resource files
│   │   └── i18n/        # Internationalization files
│   ├── templates/        # Report templates
│   └── utils/           # Utility functions
├── checkpoints/          # Model checkpoints
├── docs/                 # Documentation directory
├── pic/                  # Example images
│   ├── higher-resolution/
│   └── lower-resolution/
├── scripts/             # Maintenance scripts
└── src/                 # Source code
    ├── data/           # Data processing
    ├── models/         # Model implementation
    └── ops/            # Operator implementation
```

## Technology Stack
- **Deep Learning Framework**: PyTorch 1.9+
- **Image Processing**: OpenCV 4.5+
- **GUI Framework**: PyQt5
- **Data Processing**: NumPy, Pandas
- **Visualization**: Matplotlib
- **Internationalization**: Qt Linguist

## Feature Status

### Completed Features
- [x] Basic Image Analysis
  - Single image analysis
  - Batch image processing
  - Colony counting and statistics
- [x] Result Visualization
  - Distribution histogram
  - Count sequence graph
  - Confidence distribution
  - Multi-image comparison
- [x] Data Export
  - CSV format export
  - Excel export (with statistics)
  - JSON format export
  - Chart export (PNG/PDF)
- [x] Interface Features
  - File selection dialog import
  - Image list management
  - Result preview
  - Internationalization (Chinese/English)

### Planned Features
- [ ] Advanced Analysis
  - Species classification
  - Growth curve analysis
  - Antibiotic sensitivity testing
- [ ] Interface Optimization
  - Fluent Design migration
  - Dark mode support
  - Drag-and-drop support
- [ ] Data Management
  - Local database storage
  - History record management
  - Batch import/export

## Installation Guide

### System Requirements
- Windows 10/11 (64-bit)
- Python 3.8+
- CUDA 11.0+ (optional, for GPU acceleration)
- 8GB+ RAM
- 500MB disk space

### Installation Steps
1. Clone Repository
```bash
git clone https://github.com/your-username/CNN-.git
cd CNN-
```

2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install Dependencies
```bash
pip install -r requirements.txt
```

4. Download Models
```bash
python scripts/download_models.py
```

## Usage Instructions

### Launch Application
```bash
python app/main.py
```

### Basic Operations
1. Import images via "File" menu or drag-and-drop
2. Select analysis mode (single/batch)
3. Click "Start Analysis" button
4. View results and export report

### Important Notes
- Supported image formats: JPG, PNG
- Recommended resolution: ≥8MP
- Batch processing limit: 100 images
- Single file size limit: 20MB

## License

This project uses a dual-licensing model:

### Open Source License
For non-commercial use such as research and education, this project is licensed under the [GNU Affero General Public License v3.0](LICENSE). This license requires:

1. Any modifications and distributions must be open source
2. Source code must be available when used in network services
3. Original copyright notice must be retained
4. No warranty is provided

### Commercial License (Template/Not Implemented)
Commercial use requires obtaining a commercial license. [View commercial license details](COMMERCIAL_LICENSE.md)

Commercial license includes:
- AGPL-3.0 open source requirement exemption
- Permission for closed source use and modification
- Technical support and customization services
- Patent rights

**Note**: The commercial licensing system is currently under development and not yet implemented. Commercial use applications are not being accepted at this time. Specific terms and pricing strategies will be adjusted based on actual requirements.

Contact Information (To be updated):
- Email: [commercial@example.com](mailto:commercial@example.com)
- Phone: +86-XXX-XXXX-XXXX

## Font License Declaration

This project uses the Xiaomi MiSans font. According to the "MiSans Font Intellectual Property License Agreement":

1. This software uses the MiSans font
2. MiSans font intellectual property rights belong to Xiaomi Technology Co., Ltd.
3. This software only uses MiSans font for interface display, not for separate distribution or commercial use
4. Font license details: [Xiaomi Font License Agreement](https://hyperos.mi.com/font)

Xiaomi grants this project a non-transferable, non-exclusive, royalty-free, revocable, worldwide copyright license to use the MiSans font under the terms of the agreement.

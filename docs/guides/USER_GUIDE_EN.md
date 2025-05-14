# Colony Analysis System User Guide

## Introduction

The Colony Analysis System is a professional image analysis tool designed for automatic detection and counting of colonies in petri dishes. The system supports real-time camera preview, automatic analysis, and data export functions.

## Key Features

1. Real-time camera preview and capture
2. Automatic colony detection and counting
3. Data analysis and visualization
4. Results export and sharing

## Quick Start

### 1. Launch Application

- Double-click the application icon
- Wait for system initialization

### 2. Capture Image

1. Click the camera button at the bottom center
2. Adjust petri dish position within frame
3. Observe level indicator:
   - Green border indicates tilt within 5 degrees
   - Red border indicates adjustment needed
4. Press capture button

### 3. Analyze Image

1. Auto-enters analysis mode after capture
2. Wait for automatic analysis (few seconds)
3. View results:
   - Total colony count
   - Position markers
   - Size distribution
   - Confidence metrics

### 4. Export Results

Supports multiple formats:
- JSON (raw data)
- CSV/Excel (tabular data)
- PDF report (with images and analysis)
- Markdown document

## Interface Guide

### Main Layout

```
+------------------------+
|    Tools & Settings    | -> Top toolbar
+------------------------+
|                        |
|   Preview/Analysis     | -> Main content
|                        |
|                        |
+------------------------+
| History [CAM] Settings | -> Bottom nav
+------------------------+
```

### Function Areas

1. **Top Toolbar**
   - Parameter adjustments
   - Model selection
   - Export options

2. **Main Content**
   - Camera preview
   - Analysis results
   - Data visualization

3. **Bottom Navigation**
   - History records
   - Camera control
   - System settings

## Operation Guide

### 1. Image Capture

#### Best Practices
- Ensure adequate, uniform lighting
- Keep petri dish level
- Avoid reflections and shadows
- Use appropriate background

#### Capture Steps
1. Place petri dish on flat surface
2. Open camera preview
3. Adjust angle until green border shows
4. Capture when image is clear

### 2. Data Management

#### Project Files
- Uses `.colony` extension
- Contains original images and analysis
- Supports batch import/export

#### History
- Time-ordered
- Search and filter support
- Batch comparison

### 3. Result Analysis

#### View Data
- Overall statistics
- Distribution charts
- Confidence analysis
- Time trends

#### Export Data
1. Select records
2. Choose format
3. Specify save location
4. Confirm export

## Common Issues

### 1. Capture Issues

**Q: Why is the border always red?**
A: Check device leveling, adjust angle until level indicator shows ±5 degrees.

**Q: Blurry images?**
A: Ensure clean lens, stable device, adjust focus.

### 2. Analysis Issues

**Q: Inaccurate detection?**
A: Check lighting conditions, image clarity, adjust parameters if needed.

**Q: Slow analysis?**
A: May be due to high resolution or system resources, adjust settings.

### 3. Export Issues

**Q: Cannot export files?**
A: Check storage permissions and space.

**Q: PDF won't open?**
A: Ensure PDF reader installed, check file integrity.

## Advanced Features

### 1. Batch Processing
- Multiple image analysis
- Automatic summary reports
- Batch export capability

### 2. Custom Analysis
- Parameter adjustment
- Model selection
- Threshold settings

### 3. Data Sync
- Multi-device sync
- Cloud backup
- Real-time collaboration

## Security Notes

1. Data Security
   - Regular backups
   - Project file management
   - Timely synchronization

2. Usage Guidelines
   - Keep equipment clean
   - Regular updates
   - Follow protocols

## Support Contact

- Technical Support: support@example.com
- Issue Reporting: issues.github.com
- User Community: forum.example.com

## Version History

### V2.0.0 (2025/4)
- Added real-time preview
- Improved analysis algorithm
- Enhanced UI
- Added batch processing

### V1.5.0 (2024/12)
- Added data export
- Performance optimization
- Bug fixes

### V1.0.0 (2024/6)
- Initial release
- Basic analysis
- Data management

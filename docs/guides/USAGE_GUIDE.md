# Usage Guide

## Getting Started

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/CNN-.git
   cd CNN-
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
Navigate to the `app` directory and run:
```bash
python -m app.main
```

## New Version (app/)

This version utilizes PySide6 and the PyOneDark theme for a modern and efficient user interface.

### Key Features:
- **Modern UI**: Sleek, dark-themed interface designed for ease of use.
- **Performance**: Optimized for speed and responsiveness.
- **Cross-Platform**: Consistent experience across Windows, macOS, and Linux.
- **Customizable**: Theme and layout options for personalized use.

## Basic Operations

### Importing Images
- **Drag and Drop**: Drag image files or folders directly onto the main window.
- **File Menu**: Use the "Open File" or "Open Folder" options.
- **Clipboard**: Copy and paste images from the clipboard.

### Analysis Modes
- **Single Image Analysis**: Process individual images for detailed results.
- **Batch Analysis**: Analyze multiple images simultaneously for efficiency.
- **Real-time Analysis** (Future): Process live camera feed for immediate feedback.

### Viewing Results
- **Interactive Charts**: Visualize data with customizable plots.
- **Data Table**: View detailed results in a sortable table.
- **Statistics**: Access key metrics and summary information.
- **Comparison View**: Compare results across multiple images.

### Exporting Data
- **CSV**: Export raw data in comma-separated values format.
- **Excel**: Generate detailed reports with statistics and charts.
- **JSON**: Export data in a structured, machine-readable format.
- **Plots**: Save individual charts or combined figures.

## Advanced Features

### Analysis Settings
- **Detection Threshold**: Adjust sensitivity for colony detection.
- **Processing Parameters**: Fine-tune image processing algorithms.
- **Batch Processing**: Configure settings for batch analysis.

### Result Management
- **History**: View and manage previous analysis results.
- **Database Storage**: Store results in a local database for later retrieval.
- **Batch Import/Export**: Manage large datasets efficiently.

### Customization
- **Layout**: Rearrange and resize interface components.
- **Shortcuts**: Define custom keyboard shortcuts for common actions.
- **File Associations**: Set the application as the default for supported image types.
- **Export Templates**: Customize report formats.

## Tips and Tricks

### Performance Optimization
- **GPU Acceleration**: Enable GPU processing for faster analysis.
- **Batch Processing**: Utilize batch mode for large datasets.
- **Memory Management**: Adjust settings to optimize memory usage.

### Result Accuracy
- **Image Quality**: Ensure high-quality images for optimal results.
- **Parameter Tuning**: Experiment with settings to improve detection accuracy.
- **Troubleshooting**: Address common issues with image processing.

### Data Management
- **Regular Backups**: Protect your data with regular backups.
- **Result Organization**: Implement a system for organizing and managing results.
- **Storage Space**: Monitor and manage disk space usage.

## Troubleshooting

### Common Issues
1. **Application Startup Failure**:
   - Check system requirements.
   - Verify installation integrity.
2. **Detection Anomalies**:
   - Adjust image quality.
   - Fine-tune analysis parameters.
3. **Export Errors**:
   - Ensure sufficient disk space.
   - Check file permissions.
4. **Performance Problems**:
   - Enable GPU acceleration.
   - Optimize batch processing settings.

### Getting Help
- **Log Files**: Check application logs for detailed error messages.
- **Issue Reporting**: Submit bug reports via GitHub Issues.
- **Contact Support**: Reach out to the development team for assistance.

## Best Practices

### Workflow
1. **Image Acquisition**: Follow standardized protocols for image capture.
2. **Pre-Analysis**: Prepare images and configure settings.
3. **Result Validation**: Verify analysis results for accuracy.
4. **Data Management**: Organize and back up your data regularly.

### Efficiency
- **Keyboard Shortcuts**: Utilize shortcuts for common operations.
- **Batch Processing**: Process multiple images simultaneously.
- **Templates**: Use templates for consistent reporting.
- **Automation**: Automate repetitive tasks with scripts.

### Quality Control
- **Regular Calibration**: Ensure consistent results with periodic calibration.
- **Result Verification**: Implement a process for validating analysis results.
- **Data Backup**: Protect your data with regular backups.
- **Version Updates**: Stay up-to-date with the latest software releases.

## Appendix

### Keyboard Shortcuts
- **Ctrl+O**: Open File
- **Ctrl+S**: Save Results
- **Ctrl+P**: Print Report
- **F5**: Refresh View

### File Formats
- **Supported Image Formats**: JPG, PNG
- **Export File Formats**: CSV, Excel, JSON, PDF, PNG
- **Configuration File**: YAML

### System Requirements
- **Operating System**: Windows 10/11 (64-bit), macOS 10.15+, Linux (Ubuntu 20.04+)
- **Hardware**: 8GB+ RAM, 500MB Disk Space, (Optional) CUDA-compatible GPU
- **Dependencies**: Python 3.9+, PySide6, PyOneDark, and other libraries listed in `requirements.txt`

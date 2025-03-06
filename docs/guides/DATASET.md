# Dataset Description

## Demo Model Dataset

The demo model included in this software is trained using the AGAR dataset:

- **Dataset Name**: AGAR (Annotated Germs for Automated Recognition Dataset)
- **License**: Creative Commons Attribution-NonCommercial 2.0 Generic License (CC BY-NC 2.0)
- **Source**: https://agar.neurosys.com/
- **Usage**: For academic research and demonstration purposes only

### Dataset Details
- High-resolution microscopic images of bacterial colonies
- Multiple culture conditions and growth stages
- Detailed annotations of colony counts and locations

## Production Dataset

The production dataset is developed and maintained by the undergraduate team at the College of Agriculture and Biotechnology, Yunnan Agricultural University:

### Data Acquisition Standards
- Resolution: Supports 20MP and 8MP images
- Background: Standardized Pantone color calibration board
- Lighting: Multiple conditions (brightfield, darkfield, fluorescence)

### Data Categories
1. **Bacterial Colonies**
   - Standard culture plates
   - Different growth stages
   - Multiple bacterial species

2. **Antimicrobial Susceptibility Testing**
   - Inhibition zone measurement
   - Multiple antibiotic types
   - Time-series observation

3. **Morphological Features**
   - Colony shape and patterns
   - Color changes
   - Growth characteristics

### Future Expansion
1. **Wild Fungi Identification**
   - Macroscopic morphology
   - Habitat information
   - Safety classification

2. **Clinical Microbiology Analysis**
   - Pathogen identification
   - Antibiotic resistance patterns
   - Growth rate analysis

## Data Acquisition Guidelines

### Image Acquisition Requirements
1. **Equipment**
   - High-resolution camera for laboratory use (20MP)
   - Portable camera for fieldwork (8MP)
   - Standard color calibration board

2. **Environment**
   - Controlled lighting conditions
   - Temperature: 20-25°C
   - Humidity: 40-60%

3. **Documentation**
   - Sample metadata recording
   - Growth condition parameters
   - Time and date stamps

### Quality Control
1. **Image Quality**
   - Focus and clarity checks
   - Color calibration verification
   - Resolution validation

2. **Annotation Standards**
   - Double-blind verification
   - Expert review process
   - Version control

## Usage and Access

### Demo Dataset
- Freely available for academic research
- Compliance with CC BY-NC 2.0 license terms
- Citation required for academic use

### Production Dataset
- Patent pending
- Restricted access
- Commercial license required

## Future Development

1. **Dataset Expansion**
   - Increasing bacterial species
   - More growth conditions
   - Diverse environmental factors

2. **Standardization**
   - Protocol documentation
   - Quality metrics
   - Validation procedures

3. **Integration Plans**
   - Cloud database development
   - API access implementation
   - Collaborative research support

## New Version Notes
The new version (app/) uses PySide6 and the PyOneDark theme, providing a more modern user interface and improved performance.

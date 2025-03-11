#!/usr/bin/env python3
"""
Generate QM Translation Files
This script converts .ts translation files to .qm format
"""
import os
import sys
import subprocess
import logging
from typing import List

logger = logging.getLogger(__name__)

def find_lrelease() -> str:
    """Find lrelease executable"""
    # Try PyQt6 lrelease first
    try:
        import PyQt6
        qt_bin_dir = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'bin')
        if os.name == 'nt':  # Windows
            lrelease = os.path.join(qt_bin_dir, 'lrelease.exe')
        else:  # Unix-like
            lrelease = os.path.join(qt_bin_dir, 'lrelease')
        if os.path.exists(lrelease):
            return lrelease
    except ImportError:
        pass

    # Try system lrelease
    try:
        if subprocess.run(['lrelease', '-version'], capture_output=True).returncode == 0:
            return 'lrelease'
    except FileNotFoundError:
        pass

    # Try common installation paths
    common_paths = []
    if os.name == 'nt':  # Windows
        common_paths += [
            r'C:\Qt\6.6.1\msvc2019_64\bin\lrelease.exe',
            r'C:\Qt\6.6.0\msvc2019_64\bin\lrelease.exe',
            r'C:\Qt\6.5.3\msvc2019_64\bin\lrelease.exe'
        ]
    else:  # Unix-like
        common_paths += [
            '/usr/bin/lrelease',
            '/usr/local/bin/lrelease'
        ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("Could not find lrelease executable")

def generate_qm_files(ts_dir: str, qm_dir: str) -> bool:
    """Generate .qm files from .ts files"""
    try:
        # Create QM directory if it doesn't exist
        os.makedirs(qm_dir, exist_ok=True)

        # Find all .ts files
        ts_files = []
        for file in os.listdir(ts_dir):
            if file.endswith('.ts'):
                ts_files.append(os.path.join(ts_dir, file))

        if not ts_files:
            logger.warning("No .ts files found in %s", ts_dir)
            return False

        # Find lrelease executable
        lrelease = find_lrelease()
        logger.info("Using lrelease: %s", lrelease)

        # Convert each .ts file to .qm
        for ts_file in ts_files:
            base_name = os.path.splitext(os.path.basename(ts_file))[0]
            qm_file = os.path.join(qm_dir, f"app_{base_name}.qm")
            
            cmd = [lrelease, ts_file, '-qm', qm_file]
            logger.info("Running: %s", ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("Error converting %s: %s", ts_file, result.stderr)
                continue
                
            logger.info("Generated %s", qm_file)

        return True

    except Exception as e:
        logger.exception("Error generating QM files: %s", e)
        return False

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Get paths relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ts_dir = os.path.join(base_dir, 'app', 'resources', 'i18n')
    qm_dir = os.path.join(base_dir, 'app', 'resources', 'translations')

    logger.info("Generating QM files")
    logger.info("TS directory: %s", ts_dir)
    logger.info("QM directory: %s", qm_dir)

    if generate_qm_files(ts_dir, qm_dir):
        logger.info("Successfully generated QM files")
        return 0
    else:
        logger.error("Failed to generate QM files")
        return 1

if __name__ == '__main__':
    sys.exit(main())

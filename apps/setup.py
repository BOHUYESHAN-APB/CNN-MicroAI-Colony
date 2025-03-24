"""
Setup script for the application
应用程序安装脚本
"""
from setuptools import setup, find_packages

setup(
    name="microai-colony",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'numpy',
        'opencv-python',
        'PyQt6',
        'torch',
        'torchvision'
    ],
    entry_points={
        'console_scripts': [
            'microai=app.main:main',
        ],
    },
    package_data={
        'app': [
            'resources/config.json',
            'resources/i18n/*.json',
            'resources/models/*.pth'
        ],
    }
)

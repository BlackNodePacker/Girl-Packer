#!/usr/bin/env python3
"""
Setup script for Girl Packer
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read requirements
def read_requirements():
    with open('requirements_final_compatible.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Get data files
def get_data_files():
    data_files = []
    # Include assets
    if os.path.exists('assets'):
        for root, dirs, files in os.walk('assets'):
            if files:
                data_files.append((root, [os.path.join(root, f) for f in files]))

    # Include database
    if os.path.exists('database'):
        for root, dirs, files in os.walk('database'):
            if files:
                data_files.append((root, [os.path.join(root, f) for f in files]))

    # Include style
    if os.path.exists('gui/style.qss'):
        data_files.append(('gui', ['gui/style.qss']))

    return data_files

setup(
    name="girl-packer",
    version="1.0.0",
    description="PySide6-based GUI tool for processing media assets into Ren'Py game content",
    author="Ahmed Asker",
    author_email="ahmedasker115@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    data_files=get_data_files(),
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'girl-packer=main:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Games/Entertainment",
    ],
    python_requires=">=3.11",
)
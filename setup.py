"""
PyRiichi - Python Japanese Mahjong Engine
Setup configuration for package distribution.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from __init__.py
version = "0.1.0"
init_file = Path(__file__).parent / "pyriichi" / "__init__.py"
if init_file.exists():
    for line in init_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="pyriichi",
    version=version,
    description="A complete implementation of Japanese Mahjong (Riichi Mahjong) rules engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PyRiichi Contributors",
    author_email="",
    url="https://github.com/yourusername/pyriichi",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies required for core functionality
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Games/Entertainment :: Board Games",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="mahjong riichi japanese game engine",
    project_urls={
        "Documentation": "https://github.com/yourusername/pyriichi#readme",
        "Bug Reports": "https://github.com/yourusername/pyriichi/issues",
        "Source": "https://github.com/yourusername/pyriichi",
    },
)


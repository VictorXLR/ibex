#!/usr/bin/env python3
"""
IBEX Setup Script
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="ibex-ai",
    version="1.0.0",
    author="IBEX Development Team",
    author_email="",
    description="Intelligent Development Companion with AI-powered monitoring",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ibex-ai/ibex",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.7.0",
        "watchdog>=3.0.0",
        "openai>=1.0.0",
        "anthropic>=0.30.0",
        "ollama>=0.3.0",
        "gitpython>=3.1.0",
        "flask>=2.0.0",
        "requests>=2.25.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
        ],
        "all": [
            "openai>=1.0.0",
            "anthropic>=0.30.0",
            "ollama>=0.3.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ibex=ibex.cli:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

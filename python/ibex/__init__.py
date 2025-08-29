"""
IBEX - Intelligent Development Companion

A tool for monitoring code changes, providing AI-powered insights,
and maintaining development workflow intelligence.
"""

__version__ = "1.0.0"
__author__ = "IBEX Development Team"

from .cli import app
from .ai import AIManager

__all__ = ["app", "AIManager"]

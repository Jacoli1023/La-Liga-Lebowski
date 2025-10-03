#!/usr/bin/env python3
"""
La Liga Lebowski Fantasy Football Simulator
Main entry point for the application
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli.interface import cli

if __name__ == '__main__':
    cli()

"""
DartConnect Statistics Generator

A Python package for processing DartConnect league data and generating PDF reports.
"""

__version__ = "1.0.0"
__author__ = "Steven McDowall"
__email__ = "sjm@hawoods.org"

from .config import Config
from .data_processor import DataProcessor
from .pdf_generator import PDFGenerator

__all__ = ["Config", "DataProcessor", "PDFGenerator"]

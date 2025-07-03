# DICOM_Tool/__init__.py

from .converter import main as convert_e2e
from .extractor import main as extract_dicom

__all__ = ['convert_e2e', 'extract_dicom']

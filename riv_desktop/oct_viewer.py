import pydicom
import numpy as np
from PyQt6.QtGui import QImage
from enum import Enum

class Tool(Enum):
    VIEW = "view"
    COMPARE = "compare"
    ANNOTATE = "annotate"
    TAG = "tag"

class OCTModel:
    def __init__(self):
        self.dicom_data = None
        self.comparison_data = None
        self.current_slice = 0
        self.active_tool = Tool.VIEW

    def _clean_dicom_data(self, dataset):
        """Clean and validate DICOM metadata"""
        try:
            # Fix common issues with Photometric Interpretation
            if hasattr(dataset, 'PhotometricInterpretation'):
                # Clean up any null characters or whitespace
                cleaned_pi = dataset.PhotometricInterpretation.strip().split('\x00')[0]
                dataset.PhotometricInterpretation = cleaned_pi
            
            # If still not set, default to MONOCHROME2
            if not hasattr(dataset, 'PhotometricInterpretation'):
                dataset.PhotometricInterpretation = 'MONOCHROME2'
            
            return dataset
        except Exception as e:
            print(f"Warning: Error cleaning DICOM data: {str(e)}")
            return dataset

    def _get_pixel_data(self, dataset):
        """Safely extract pixel data from DICOM dataset"""
        try:
            return dataset.pixel_array
        except Exception as e:
            # Try alternative approach if standard method fails
            try:
                raw_data = dataset.PixelData
                if hasattr(dataset, 'Rows') and hasattr(dataset, 'Columns'):
                    shape = (dataset.Rows, dataset.Columns)
                    return np.frombuffer(raw_data, dtype=np.uint16).reshape(shape)
                else:
                    raise ValueError("Cannot determine image dimensions")
            except Exception as nested_e:
                raise ValueError(f"Failed to extract pixel data: {str(e)}, {str(nested_e)}")

    def load_file(self, filename):
        try:
            dataset = pydicom.dcmread(filename)
            dataset = self._clean_dicom_data(dataset)
            
            # Test pixel data access
            _ = self._get_pixel_data(dataset)
            
            self.dicom_data = dataset
            self.current_slice = 0
            return True, ""
        except Exception as e:
            return False, f"Error loading DICOM: {str(e)}"

    def get_total_slices(self):
        if self.dicom_data is None:
            return 0
        try:
            pixel_data = self._get_pixel_data(self.dicom_data)
            if len(pixel_data.shape) > 2:
                return pixel_data.shape[0]
            return 1
        except Exception:
            return 0

    def get_slice_image(self, slice_num) -> QImage:
        if self.dicom_data is None:
            return None

        try:
            pixel_data = self._get_pixel_data(self.dicom_data)
            
            # Get the slice data, handling both single and multi-slice
            if len(pixel_data.shape) > 2:
                image_data = pixel_data[slice_num]
            else:
                image_data = pixel_data

            # Handle division by zero case
            data_min = float(np.min(image_data))
            data_max = float(np.max(image_data))
            
            if data_max == data_min:
                normalized_data = np.zeros_like(image_data)
            else:
                normalized_data = ((image_data.astype(float) - data_min) / 
                                 (data_max - data_min) * 255.0)
            
            image_data = normalized_data.astype(np.uint8)
            
            # Convert to QImage
            height, width = image_data.shape
            bytes_per_line = width
            return QImage(image_data.data, width, height, 
                        bytes_per_line, QImage.Format.Format_Grayscale8)
        except Exception as e:
            print(f"Error getting slice image: {str(e)}")
            return None

    def load_comparison_file(self, filename):
        try:
            self.comparison_data = pydicom.dcmread(filename)
            return True, ""
        except Exception as e:
            return False, str(e)

    def get_comparison_slice_image(self, slice_num) -> QImage:
        if self.comparison_data is None:
            return None

        # Get the slice data, handling both single and multi-slice
        if len(self.comparison_data.pixel_array.shape) > 2:
            image_data = self.comparison_data.pixel_array[slice_num]
        else:
            image_data = self.comparison_data.pixel_array

        # Handle division by zero case
        data_min = image_data.min()
        data_max = image_data.max()
        if data_max == data_min:
            normalized_data = np.zeros_like(image_data)
        else:
            normalized_data = ((image_data - data_min) / (data_max - data_min) * 255)
        
        image_data = normalized_data.astype(np.uint8)
        
        # Convert to QImage
        height, width = image_data.shape
        bytes_per_line = width
        return QImage(image_data.data, width, height, 
                     bytes_per_line, QImage.Format.Format_Grayscale8)

    def has_comparison(self):
        return self.comparison_data is not None
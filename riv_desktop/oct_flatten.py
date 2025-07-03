import numpy as np
import cv2
from scipy import ndimage
from scipy.signal import find_peaks
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def flatten_oct_image(image: np.ndarray) -> np.ndarray:
    """
    Basic OCT image flattening algorithm.
    
    Args:
        image: Input OCT image as numpy array
        
    Returns:
        Flattened OCT image
    """
    try:
        logger.info("Applying basic OCT flattening algorithm")
        
        # Ensure image is 2D
        if len(image.shape) > 2:
            image = np.mean(image, axis=2)
        
        # Convert to float for processing
        img_float = image.astype(np.float32)
        
        # Normalize image
        img_normalized = (img_float - np.min(img_float)) / (np.max(img_float) - np.min(img_float))
        
        # Simple surface detection using gradient
        gradient = np.gradient(img_normalized, axis=0)
        
        # Find surface for each column
        surface_points = []
        for col in range(img_normalized.shape[1]):
            column_gradient = gradient[:, col]
            
            # Find peaks in gradient (surface candidates)
            peaks, _ = find_peaks(np.abs(column_gradient), height=0.1)
            
            if len(peaks) > 0:
                # Take the first significant peak as surface
                surface_points.append(peaks[0])
            else:
                # Fallback to top of image
                surface_points.append(0)
        
        # Smooth the surface
        surface_points = ndimage.gaussian_filter1d(surface_points, sigma=2)
        
        # Create flattened image
        flattened = np.zeros_like(img_normalized)
        
        for col in range(img_normalized.shape[1]):
            surface_row = int(surface_points[col])
            
            # Shift column to align surface
            if surface_row > 0:
                flattened[:-surface_row, col] = img_normalized[surface_row:, col]
            else:
                flattened[:, col] = img_normalized[:, col]
        
        # Convert back to original data type
        flattened_scaled = (flattened * 255).astype(np.uint8)
        
        logger.info("Basic OCT flattening completed successfully")
        return flattened_scaled
        
    except Exception as e:
        logger.error(f"Error in basic OCT flattening: {e}")
        raise

def flatten_oct_image_enhanced(image: np.ndarray) -> np.ndarray:
    """
    Enhanced OCT image flattening algorithm with better surface detection.
    
    Args:
        image: Input OCT image as numpy array
        
    Returns:
        Flattened OCT image
    """
    try:
        logger.info("Applying enhanced OCT flattening algorithm")
        
        # Ensure image is 2D
        if len(image.shape) > 2:
            image = np.mean(image, axis=2)
        
        # Convert to float for processing
        img_float = image.astype(np.float32)
        
        # Normalize image
        img_min, img_max = np.min(img_float), np.max(img_float)
        if img_max > img_min:
            img_normalized = (img_float - img_min) / (img_max - img_min)
        else:
            img_normalized = img_float
        
        # Enhanced surface detection
        surface_points = detect_retinal_surface_enhanced(img_normalized)
        
        # Apply polynomial fitting for smoother surface
        x_coords = np.arange(len(surface_points))
        try:
            # Fit polynomial to surface points
            poly_coeffs = np.polyfit(x_coords, surface_points, deg=min(3, len(surface_points)-1))
            surface_smooth = np.polyval(poly_coeffs, x_coords)
        except:
            # Fallback to Gaussian smoothing
            surface_smooth = ndimage.gaussian_filter1d(surface_points, sigma=3)
        
        # Create flattened image with interpolation
        flattened = create_flattened_image(img_normalized, surface_smooth)
        
        # Post-processing: enhance contrast
        flattened = enhance_contrast(flattened)
        
        # Convert back to uint8
        flattened_scaled = (flattened * 255).astype(np.uint8)
        
        logger.info("Enhanced OCT flattening completed successfully")
        return flattened_scaled
        
    except Exception as e:
        logger.error(f"Error in enhanced OCT flattening: {e}")
        # Fallback to basic algorithm
        logger.info("Falling back to basic OCT flattening")
        return flatten_oct_image(image)

def detect_retinal_surface_enhanced(image: np.ndarray) -> np.ndarray:
    """
    Enhanced retinal surface detection using multiple methods.
    
    Args:
        image: Normalized OCT image
        
    Returns:
        Array of surface points for each column
    """
    try:
        height, width = image.shape
        surface_points = np.zeros(width)
        
        # Method 1: Gradient-based detection
        gradient_y = np.gradient(image, axis=0)
        
        # Method 2: Intensity-based detection
        for col in range(width):
            column = image[:, col]
            gradient_col = gradient_y[:, col]
            
            # Find strong positive gradients (dark to bright transitions)
            strong_gradients = np.where(gradient_col > 0.1)[0]
            
            if len(strong_gradients) > 0:
                # Take the first strong gradient as surface
                surface_points[col] = strong_gradients[0]
            else:
                # Fallback: find maximum intensity in upper portion
                upper_portion = column[:height//3]
                if len(upper_portion) > 0:
                    surface_points[col] = np.argmax(upper_portion)
                else:
                    surface_points[col] = 0
        
        # Remove outliers using median filtering
        surface_filtered = ndimage.median_filter(surface_points, size=5)
        
        return surface_filtered
        
    except Exception as e:
        logger.error(f"Error in surface detection: {e}")
        # Fallback to simple surface detection
        return np.zeros(image.shape[1])

def create_flattened_image(image: np.ndarray, surface_points: np.ndarray) -> np.ndarray:
    """
    Create flattened image by aligning surface points.
    
    Args:
        image: Input OCT image
        surface_points: Detected surface points for each column
        
    Returns:
        Flattened image
    """
    try:
        height, width = image.shape
        flattened = np.zeros_like(image)
        
        # Calculate reference surface level (median)
        reference_level = int(np.median(surface_points))
        
        for col in range(width):
            surface_row = int(surface_points[col])
            shift = reference_level - surface_row
            
            # Apply shift with bounds checking
            if shift > 0:
                # Shift down
                end_idx = min(height, height - shift)
                flattened[shift:, col] = image[:end_idx, col]
            elif shift < 0:
                # Shift up
                start_idx = abs(shift)
                flattened[:height+shift, col] = image[start_idx:, col]
            else:
                # No shift needed
                flattened[:, col] = image[:, col]
        
        return flattened
        
    except Exception as e:
        logger.error(f"Error creating flattened image: {e}")
        return image

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    Enhance contrast of the flattened OCT image.
    
    Args:
        image: Input image
        
    Returns:
        Contrast-enhanced image
    """
    try:
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        if cv2 is not None:
            # Convert to uint8 for CLAHE
            img_uint8 = (image * 255).astype(np.uint8)
            
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(img_uint8)
            
            # Convert back to float
            return enhanced.astype(np.float32) / 255.0
        else:
            # Fallback: simple histogram stretching
            img_min, img_max = np.percentile(image, [2, 98])
            if img_max > img_min:
                enhanced = np.clip((image - img_min) / (img_max - img_min), 0, 1)
            else:
                enhanced = image
            
            return enhanced
            
    except Exception as e:
        logger.error(f"Error enhancing contrast: {e}")
        return image

def validate_oct_image(image: np.ndarray) -> bool:
    """
    Validate if the image is suitable for OCT flattening.
    
    Args:
        image: Input image
        
    Returns:
        True if image is valid for OCT processing
    """
    try:
        # Check if image has reasonable dimensions
        if len(image.shape) < 2:
            return False
        
        height, width = image.shape[:2]
        
        # OCT images should have reasonable aspect ratio
        if height < 50 or width < 50:
            return False
        
        # Check if image has sufficient dynamic range
        img_range = np.max(image) - np.min(image)
        if img_range < 10:  # Very low contrast
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating OCT image: {e}")
        return False

# Additional utility functions for OCT processing
def preprocess_oct_image(image: np.ndarray) -> np.ndarray:
    """
    Preprocess OCT image before flattening.
    
    Args:
        image: Raw OCT image
        
    Returns:
        Preprocessed image
    """
    try:
        # Remove noise using Gaussian filter
        if len(image.shape) == 2:
            denoised = ndimage.gaussian_filter(image, sigma=0.5)
        else:
            denoised = image
        
        # Normalize intensity
        img_min, img_max = np.percentile(denoised, [1, 99])
        if img_max > img_min:
            normalized = np.clip((denoised - img_min) / (img_max - img_min), 0, 1)
        else:
            normalized = denoised
        
        return normalized
        
    except Exception as e:
        logger.error(f"Error preprocessing OCT image: {e}")
        return image

def postprocess_flattened_image(image: np.ndarray) -> np.ndarray:
    """
    Post-process flattened OCT image.
    
    Args:
        image: Flattened OCT image
        
    Returns:
        Post-processed image
    """
    try:
        # Apply slight sharpening
        if cv2 is not None:
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(image, -1, kernel)
            # Blend with original
            result = 0.8 * image + 0.2 * sharpened
        else:
            result = image
        
        # Ensure values are in valid range
        result = np.clip(result, 0, 255)
        
        return result.astype(np.uint8)
        
    except Exception as e:
        logger.error(f"Error post-processing flattened image: {e}")
        return image.astype(np.uint8)

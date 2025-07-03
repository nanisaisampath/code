from PIL import Image
import numpy as n

def apply_windowing(pixels, dicom):
    # Dummy version – replace with actual logic
    return pixels

def convert_dicom_to_image(pixels, frame):

    image = pixels if pixels.ndim == 2 else pixels[frame]
    image = Image.fromarray(image.astype('uint8'))
    return image

def save_to_cache(crc, data):
    # Dummy cache function – no-op
    print(f"[INFO] Saving to cache: {crc}")
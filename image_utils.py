"""Brightness and contrast adjustments for otolith images using Pillow."""

import cv2
import numpy as np
from PIL import Image, ImageEnhance


def adjust_image(image: Image.Image, brightness: float, contrast: float) -> Image.Image:
    """Apply brightness and contrast adjustments.

    Args:
        image: Source PIL Image.
        brightness: -50 to +50 (0 = no change). Mapped to Pillow factor 0.5-1.5.
        contrast: -50 to +50 (0 = no change). Mapped to Pillow factor 0.5-1.5.

    Returns:
        Adjusted PIL Image.
    """
    # Map slider range (-50 to +50) to Pillow factor (0.5 to 1.5)
    b_factor = 1.0 + (brightness / 100.0)
    c_factor = 1.0 + (contrast / 100.0)

    result = ImageEnhance.Brightness(image).enhance(b_factor)
    result = ImageEnhance.Contrast(result).enhance(c_factor)
    return result


def clahe_enhancement(image: Image.Image,
                      clip_limit: float = 3.0,
                      tile_size: int = 25) -> Image.Image:
    """Apply CLAHE to a single image with adaptive tile grid size."""
    gray_image = np.array(image.convert("L"))
    h, w = gray_image.shape[:2]
    grid_y = max(1, h // tile_size)
    grid_x = max(1, w // tile_size)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_x, grid_y))
    enhanced_image = clahe.apply(gray_image)
    return Image.fromarray(np.stack([enhanced_image] * 3, axis=-1))

from io import BytesIO
from typing import Dict

from PIL import Image


def summarize_image(image_bytes: bytes) -> Dict[str, str]:
    image = Image.open(BytesIO(image_bytes))
    original_format = image.format
    image = image.convert("RGB")
    width, height = image.size
    aspect_ratio = round(width / height, 2) if height else 0

    resized = image.resize((64, 64))
    pixels = list(resized.getdata())
    avg_r = sum(p[0] for p in pixels) // len(pixels)
    avg_g = sum(p[1] for p in pixels) // len(pixels)
    avg_b = sum(p[2] for p in pixels) // len(pixels)
    dominant_hex = f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}"

    return {
        "width": str(width),
        "height": str(height),
        "aspect_ratio": str(aspect_ratio),
        "dominant_color": dominant_hex,
        "format": original_format or "unknown",
        "mode": image.mode,
    }

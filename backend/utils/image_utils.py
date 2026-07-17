import base64
import io
from typing import Union
from PIL import Image
from backend.utils.logger import app_logger

def crop_image(image_path_or_bytes: Union[str, bytes], box: tuple) -> bytes:
    """
    Crops an image based on bounding box coords (x1, y1, x2, y2).
    Returns cropped image as PNG bytes.
    """
    try:
        if isinstance(image_path_or_bytes, str):
            image = Image.open(image_path_or_bytes)
        else:
            image = Image.open(io.BytesIO(image_path_or_bytes))
            
        x1, y1, x2, y2 = box
        # PIL crop expects (left, upper, right, lower)
        cropped_img = image.crop((x1, y1, x2, y2))
        
        output_buffer = io.BytesIO()
        cropped_img.save(output_buffer, format="PNG")
        return output_buffer.getvalue()
    except Exception as e:
        app_logger.error(f"Error cropping image: {e}")
        raise e

def base64_to_bytes(base64_string: str) -> bytes:
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    return base64.b64decode(base64_string)

def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")

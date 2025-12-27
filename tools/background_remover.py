# tools/background_remover.py

import cv2
import numpy as np
import os
from io import BytesIO # <<<<<< تأكد من وجوده
from tools.logger import get_logger 
from PIL import Image # تأكد من استيرادها هنا أيضاً (لأنها تستخدم في PIL.Image.open)

logger = get_logger("TransparentBackgroundRemover") 

# >>> 2. استيراد المكتبة البديلة backgroundremover <<<
BACKGROUND_REMOVER_AVAILABLE = False
try:
    from backgroundremover.bg import remove 
    BACKGROUND_REMOVER_AVAILABLE = True
except ImportError as e:
    logger.critical(f"FATAL: backgroundremover library could not be imported. Error: {e}", exc_info=True)


# تعريف القيم الأولية
_is_initialized = False

def _initialize_transparent_background():
    """هذه الدالة الآن للتحقق من التوافر فقط (لا تهيئة مُعقدة)."""
    global _is_initialized
    
    if not BACKGROUND_REMOVER_AVAILABLE:
        logger.error("backgroundremover library is unavailable. Cannot proceed.")
        return False
        
    if not _is_initialized:
        logger.info("Background Remover (backgroundremover) checked and ready.")
        _is_initialized = True
        
    return True


def remove_background(cv2_image: np.ndarray) -> np.ndarray:
    """
    يزيل الخلفية من صورة CV2 باستخدام مكتبة backgroundremover.
    """
    
    if not _initialize_transparent_background():
        logger.error("Background remover check failed. Returning original image.")
        return cv2.cvtColor(cv2_image, cv2.COLOR_BGR2BGRA)

    try:
        # 1. تحويل صورة CV2 (BGR) إلى PIL Image (RGB)
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # 2. حفظ صورة PIL مؤقتاً في كائن بايت (BytesIO)
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # 3. تطبيق إزالة الخلفية باستخدام كائن البايت
        result_bytes = remove(
            image_bytes, # تمرير البايت
            model_name="u2netp", # <<< التغيير إلى u2netp لتحسين الدقة
            alpha_matting=True, # تفعيل الماتينج
        )
        
        # 4. تحويل الناتج (وهو كائن بايت) إلى PIL Image
        result_pil = Image.open(BytesIO(result_bytes))
        
        # 5. تحويل الناتج من PIL RGBA إلى CV2 BGRA
        result_rgba = np.array(result_pil)
        
        # تحويل من RGBA إلى BGRA
        r, g, b, a = cv2.split(result_rgba)
        result_bgra = cv2.merge((b, g, r, a))
        
        return result_bgra

    except Exception as e:
        logger.error(f"Runtime error during backgroundremover processing: {e}. Returning original image with opaque alpha.", exc_info=True)
        return cv2.cvtColor(cv2_image, cv2.COLOR_BGR2BGRA)
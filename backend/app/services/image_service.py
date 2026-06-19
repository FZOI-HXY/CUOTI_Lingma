import cv2
import numpy as np
from typing import Tuple
from pathlib import Path
from app.utils.logger import logger


class ImageService:
    """图像通用工具服务

    提供图片保存和缩放等基础功能。
    版面分析和图片提取逻辑已迁移至 ocr_service.py（由 PP-StructureV3 处理）。
    """

    @staticmethod
    def save_image(image_array: np.ndarray, output_path: str) -> str:
        """保存图片数组到文件"""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            success = cv2.imwrite(output_path, image_array)
            if not success:
                raise ValueError(f"Failed to save image to: {output_path}")
            logger.debug(f"Image saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise

    @staticmethod
    def resize_image(
        image_path: str,
        max_size: Tuple[int, int] = (1920, 1080),
    ) -> str:
        """如果超过最大尺寸则缩放，否则返回原路径"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Failed to read image: {image_path}")

            h, w = img.shape[:2]
            max_w, max_h = max_size

            if w <= max_w and h <= max_h:
                return image_path

            scale = min(max_w / w, max_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            output_path = image_path.replace('.', '_resized.')
            cv2.imwrite(output_path, resized)
            logger.info(f"Image resized from ({w}x{h}) to ({new_w}x{new_h})")
            return output_path

        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            return image_path

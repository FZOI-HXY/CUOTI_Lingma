# DEPRECATED: This module is not used. Functionality has been absorbed by ocr_service.py and archive_service.py.
# Safe to remove after verifying no external references.

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from ..config import settings
from ..utils.logger import logger


class StorageService:
    """文件存储服务"""
    
    @staticmethod
    def save_markdown(content: str, filename: str) -> str:
        """保存Markdown文件"""
        try:
            output_dir = Path(settings.PROCESSED_DIR) / "markdowns"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 确保文件名以.md结尾
            if not filename.endswith('.md'):
                filename = f"{filename}.md"
            
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Markdown saved to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save markdown: {str(e)}")
            raise
    
    @staticmethod
    def save_processed_image(image_path: str, question_id: int) -> str:
        """保存处理后的图片"""
        try:
            output_dir = Path(settings.PROCESSED_DIR) / "images" / str(question_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成新文件名
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            ext = Path(image_path).suffix
            new_filename = f"processed_{timestamp}{ext}"
            new_path = output_dir / new_filename
            
            # 复制文件
            shutil.copy2(image_path, new_path)
            
            logger.info(f"Processed image saved to: {new_path}")
            return str(new_path)
            
        except Exception as e:
            logger.error(f"Failed to save processed image: {str(e)}")
            raise
    
    @staticmethod
    def cleanup_temp_files(file_path: str, keep_days: int = 7):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                file_age = datetime.now(timezone.utc) - datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc)
                
                if file_age.days > keep_days:
                    os.remove(file_path)
                    logger.info(f"Cleaned up old temp file: {file_path}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file: {str(e)}")
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """获取文件信息"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'size': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                'exists': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None


# 全局存储服务实例
storage_service = StorageService()

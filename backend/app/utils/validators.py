import uuid
import hashlib
import os
from datetime import datetime
from typing import Optional


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{timestamp}_{unique_id}{ext}"


def sanitize_filename(filename: str) -> str:
    """清理文件名,移除不安全字符"""
    # 只保留字母、数字、下划线、连字符和点
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
    sanitized = "".join(c for c in filename if c in safe_chars)
    return sanitized or "unnamed"


def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """计算文件哈希值"""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def validate_image_type(filename: str, allowed_types: list = None) -> bool:
    """验证图片类型"""
    if allowed_types is None:
        allowed_types = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_types


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小(MB)"""
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)

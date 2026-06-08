from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional
import os
import shutil
import time

from ..config import settings
from ..utils.logger import logger
from ..utils.validators import (
    generate_unique_filename,
    validate_image_type,
    get_file_size_mb
)
from ..core.exceptions import FileUploadError
from ..schemas import UploadResponse
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[int] = None
):
    """
    上传图片文件
    
    - 验证文件类型和大小
    - 生成唯一文件名
    - 保存到临时目录
    - 返回文件ID和路径
    """
    start_time = time.time()
    
    try:
        # 验证文件类型
        if not validate_image_type(file.filename):
            raise FileUploadError(
                message=f"Unsupported file type. Allowed types: JPG, PNG, BMP, TIFF, WEBP",
                details={"filename": file.filename}
            )
        
        # 读取文件内容以验证大小
        contents = await file.read()
        file_size = len(contents)
        
        # 验证文件大小
        if file_size > settings.MAX_FILE_SIZE:
            raise FileUploadError(
                message=f"File too large. Max size: {settings.MAX_FILE_SIZE / (1024*1024)}MB",
                details={"file_size": file_size, "max_size": settings.MAX_FILE_SIZE}
            )
        
        # 生成唯一文件名
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # 保存文件
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # 计算文件哈希
        from ..utils.validators import calculate_file_hash
        file_hash = calculate_file_hash(file_path)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录日志
        logger.info(f"File uploaded successfully: {unique_filename}")
        
        return UploadResponse(
            file_id=unique_filename,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type or "image/jpeg",
            message="File uploaded successfully"
        )
        
    except FileUploadError:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise FileUploadError(
            message=f"Upload failed: {str(e)}",
            details={"error": str(e)}
        )


@router.post("/batch")
async def upload_batch_images(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    user_id: Optional[int] = None
):
    """批量上传图片文件"""
    results = []
    errors = []
    
    for file in files:
        try:
            # 复用单文件上传逻辑
            contents = await file.read()
            file_size = len(contents)
            
            if file_size > settings.MAX_FILE_SIZE:
                errors.append({
                    "filename": file.filename,
                    "error": "File too large"
                })
                continue
            
            unique_filename = generate_unique_filename(file.filename)
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(contents)
            
            results.append({
                "file_id": unique_filename,
                "filename": file.filename,
                "file_path": file_path,
                "file_size": file_size
            })
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }

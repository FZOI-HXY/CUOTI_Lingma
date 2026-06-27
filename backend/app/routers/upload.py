from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import Optional
import asyncio
import os
import time

from ..config import settings
from ..utils.logger import logger
from ..utils.validators import (
    generate_unique_filename,
    validate_image_type,
    validate_image_magic_bytes,
    get_file_size_mb,
    calculate_file_hash
)
from ..core.exceptions import AppException, FileUploadError
from ..schemas import UploadResponse

router = APIRouter()


def _write_file(file_path: str, contents: bytes) -> None:
    """Synchronous file write helper for use with asyncio.to_thread()."""
    with open(file_path, "wb") as f:
        f.write(contents)


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
        
        # 流式读取文件内容，分块检查大小限制（C3: 防止内存溢出）
        chunks = []
        total_size = 0
        MAX_SIZE = settings.MAX_FILE_SIZE
        while chunk := await file.read(65536):  # 64KB chunks
            total_size += len(chunk)
            if total_size > MAX_SIZE:
                raise AppException(
                    status_code=413,
                    message=f"文件过大: 超过 {MAX_SIZE // 1024 // 1024}MB 限制"
                )
            chunks.append(chunk)
        contents = b"".join(chunks)
        file_size = total_size

        # H1: Magic byte 文件类型验证
        if not validate_image_magic_bytes(contents, file.filename):
            raise AppException(
                status_code=400,
                message=f"文件类型不匹配: {file.filename} 的内容不是有效的图片文件"
            )
        
        # 生成唯一文件名
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # 保存文件（使用 asyncio.to_thread 避免阻塞事件循环）
        await asyncio.to_thread(os.makedirs, settings.UPLOAD_DIR, exist_ok=True)
        await asyncio.to_thread(_write_file, file_path, contents)

        # 计算文件哈希（使用 asyncio.to_thread 避免阻塞事件循环）
        file_hash = await asyncio.to_thread(calculate_file_hash, file_path)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录日志
        logger.info(f"File uploaded successfully: {unique_filename} ({duration_ms:.1f}ms)")
        
        return UploadResponse(
            file_id=unique_filename,
            filename=file.filename,
            file_path=unique_filename,  # 仅返回文件名，不暴露服务器端绝对路径
            file_size=file_size,
            content_type=file.content_type or "image/jpeg",
            message="File uploaded successfully"
        )
        
    except FileUploadError:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise FileUploadError(
            message="Upload failed due to an internal error",
            details={}
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
            # 复用单文件上传逻辑 — 流式读取 + 大小限制（C3）
            chunks = []
            total_size = 0
            MAX_SIZE = settings.MAX_FILE_SIZE
            while chunk := await file.read(65536):  # 64KB chunks
                total_size += len(chunk)
                if total_size > MAX_SIZE:
                    errors.append({
                        "filename": file.filename,
                        "error": f"文件过大: 超过 {MAX_SIZE // 1024 // 1024}MB 限制"
                    })
                    break
                chunks.append(chunk)
            else:
                # Only process if we didn't break (file within size limit)
                contents = b"".join(chunks)
                file_size = total_size

                # H1: Magic byte 文件类型验证
                if not validate_image_magic_bytes(contents, file.filename):
                    errors.append({
                        "filename": file.filename,
                        "error": f"文件类型不匹配: 内容不是有效的图片文件"
                    })
                    continue

                if not validate_image_type(file.filename):
                    errors.append({
                        "filename": file.filename,
                        "error": "Unsupported file type"
                    })
                    continue

                unique_filename = generate_unique_filename(file.filename)
                file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

                await asyncio.to_thread(os.makedirs, settings.UPLOAD_DIR, exist_ok=True)
                await asyncio.to_thread(_write_file, file_path, contents)

                results.append({
                    "file_id": unique_filename,
                    "filename": file.filename,
                    "file_size": file_size
                })
            
        except Exception as e:
            logger.error(f"Batch upload failed for {file.filename}: {str(e)}")
            errors.append({
                "filename": file.filename,
                "error": "Upload failed"
            })
    
    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }

"""
PDF 上传与处理路由 —— 接收 PDF 文件，逐页渲染为图片后送入 OCR 管线。
"""

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from typing import Optional
import asyncio
import os
import time
import uuid

from ..config import settings
from ..utils.logger import logger
from ..utils.validators import (
    generate_unique_filename,
    validate_pdf_type,
    validate_pdf_magic_bytes,
    calculate_file_hash,
)
from ..core.exceptions import AppException, FileUploadError
from ..schemas import PDFUploadResponse, PDFPageTask
from ..services.pdf_service import pdf_service
from ..database import get_db, get_db_session
from ..models import Question, ProcessingLog, TaskStatus
from sqlalchemy.orm import Session

router = APIRouter()


def _write_file(file_path: str, contents: bytes) -> None:
    """同步文件写入"""
    with open(file_path, "wb") as f:
        f.write(contents)


@router.post("/pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_vl: Optional[bool] = False,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    上传 PDF 文件并逐页送入 OCR 处理。

    流程：
    1. 验证文件类型、magic bytes、大小
    2. 保存 PDF 到 UPLOAD_DIR
    3. 渲染每页为 PNG
    4. 为每页创建 Question + TaskStatus 记录
    5. 为每页启动后台 OCR 任务
    6. 返回任务列表
    """
    start_time = time.time()

    try:
        # ── 1. 验证文件类型 ──
        if not validate_pdf_type(file.filename):
            raise FileUploadError(
                message="Only PDF files are accepted",
                details={"filename": file.filename},
            )

        # ── 2. 流式读取（分块检查大小） ──
        chunks = []
        total_size = 0
        MAX_SIZE = settings.PDF_MAX_FILE_SIZE
        while chunk := await file.read(65536):
            total_size += len(chunk)
            if total_size > MAX_SIZE:
                raise AppException(
                    status_code=413,
                    message=f"PDF 文件过大: 超过 {MAX_SIZE // 1024 // 1024}MB 限制",
                )
            chunks.append(chunk)
        contents = b"".join(chunks)

        # ── 3. Magic bytes 验证 ──
        if not validate_pdf_magic_bytes(contents):
            raise AppException(
                status_code=400,
                message=f"文件类型不匹配: {file.filename} 不是有效的 PDF 文件",
            )

        # ── 4. 保存 PDF ──
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        await asyncio.to_thread(os.makedirs, settings.UPLOAD_DIR, exist_ok=True)
        await asyncio.to_thread(_write_file, file_path, contents)

        # ── 5. 渲染页面为图片 ──
        page_results = await asyncio.to_thread(
            pdf_service.render_pages_to_images,
            pdf_path=file_path,
            output_dir=settings.UPLOAD_DIR,
            file_prefix=os.path.splitext(unique_filename)[0],
        )

        if not page_results:
            raise AppException(
                status_code=400,
                message="PDF 文件没有可处理的页面",
            )

        # ── 6. 为每页创建 Question + TaskStatus，并注册后台 OCR ──
        page_tasks: list[PDFPageTask] = []

        for page_info in page_results:
            task_id = str(uuid.uuid4())

            question = Question(
                user_id=user_id,
                original_image_path=page_info["image_filename"],
                status="processing",
            )
            db.add(question)
            db.flush()

            task_status = TaskStatus(
                task_id=task_id,
                question_id=question.id,
                status="processing",
                progress=0,
                message="Processing started",
            )
            db.add(task_status)

            log = ProcessingLog(
                user_id=user_id,
                question_id=question.id,
                action="pdf_page_ocr",
                level="INFO",
                message=f"PDF page {page_info['page_number']} OCR started (source: {unique_filename})",
            )
            db.add(log)

            db.flush()

            page_tasks.append(
                PDFPageTask(
                    page_number=page_info["page_number"],
                    task_id=task_id,
                    question_id=question.id,
                    page_image_id=page_info["image_filename"],
                )
            )

            # 注册后台 OCR 任务（复用现有 OCR 流程）
            from ..routers.ocr import execute_ocr_processing

            background_tasks.add_task(
                execute_ocr_processing,
                task_id=task_id,
                question_id=question.id,
                file_id=page_info["image_filename"],
                use_vl=use_vl or False,
            )

        db.commit()

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"PDF uploaded: {unique_filename}, {len(page_tasks)} pages, "
            f"rendered in {duration_ms:.0f}ms"
        )

        return PDFUploadResponse(
            file_id=unique_filename,
            filename=file.filename,
            total_pages=len(page_tasks),
            pages=page_tasks,
            message=f"PDF uploaded: {len(page_tasks)} pages processing started",
        )

    except (FileUploadError, AppException):
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"PDF upload failed: {e}", exc_info=True)
        raise FileUploadError(
            message="PDF upload failed due to an internal error",
            details={},
        )

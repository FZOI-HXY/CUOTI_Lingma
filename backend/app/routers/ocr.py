from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Optional
import uuid
import time
import os
from datetime import datetime

from ..services.ocr_service import ocr_service
from ..services.vl_service import vl_service
from ..core.exceptions import OCRProcessingError
from ..schemas import OCRProcessRequest, OCRProcessResponse
from ..database import get_db, get_db_session
from ..models import Question, ProcessingLog, TaskStatus
from ..config import settings as app_settings
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/process", response_model=OCRProcessResponse)
async def process_ocr(
    background_tasks: BackgroundTasks,
    request: OCRProcessRequest,
    db: Session = Depends(get_db)
):
    """
    启动OCR处理任务
    
    - 验证文件ID
    - 创建数据库记录
    - 异步执行OCR处理
    - 返回任务ID
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建错题记录
        question = Question(
            user_id=request.user_id,
            original_image_path=request.file_id,
            status="processing"
        )
        db.add(question)
        db.flush()  # 获取question.id，但不提交
        
        # 持久化任务状态到数据库（替代内存字典）
        task_status = TaskStatus(
            task_id=task_id,
            question_id=question.id,
            status="processing",
            progress=0,
            message="Processing started"
        )
        db.add(task_status)
        
        # 记录启动日志
        engine_label = "VL-1.6 (enhanced)" if request.use_vl else "PP-StructureV3"
        log = ProcessingLog(
            user_id=request.user_id,
            question_id=question.id,
            action="ocr_process",
            level="INFO",
            message=f"OCR processing started for file: {request.file_id} (engine: {engine_label})"
        )
        db.add(log)
        db.commit()
        
        # 添加后台任务 —— 不再传递db会话，由后台任务自行创建独立会话
        background_tasks.add_task(
            execute_ocr_processing,
            task_id=task_id,
            question_id=question.id,
            file_id=request.file_id,
            use_vl=request.use_vl or False
        )
        
        return OCRProcessResponse(
            task_id=task_id,
            status="processing",
            message="OCR processing started successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise OCRProcessingError(
            message=f"Failed to start OCR processing: {str(e)}",
            details={"error": str(e)}
        )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """查询任务状态（从数据库读取，而非内存字典）"""
    task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
    
    if not task:
        return {"error": "Task not found"}
    
    return {
        'task_id': task.task_id,
        'status': task.status,
        'question_id': task.question_id,
        'progress': task.progress,
        'message': task.message,
        'error': task.error,
        'processing_time_ms': task.processing_time_ms,
        'created_at': task.created_at.isoformat() if task.created_at else None,
        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
    }


@router.get("/vl/status")
async def get_vl_status():
    """查询 VL 增强模式是否可用"""
    vl_service.initialize()
    return {
        "enabled": app_settings.VL_ENABLED,
        "available": vl_service.is_available,
        "running": vl_service.is_running,
        "server_url": vl_service.server_url if app_settings.VL_ENABLED else None,
    }


async def execute_ocr_processing(
    task_id: str,
    question_id: int,
    file_id: str,
    use_vl: bool = False
):
    """
    执行OCR处理的后台任务。
    使用独立的数据库会话（get_db_session），不依赖HTTP请求的生命周期。
    
    use_vl=True 时使用 PaddleOCR-VL-1.6 增强模式，否则使用默认的 PP-StructureV3。
    """
    start_time = time.time()
    
    try:
        # 更新任务状态: 开始处理
        engine_label = "VL-1.6" if use_vl else "PP-StructureV3"
        _update_task_status(task_id, progress=10, message=f'Starting OCR ({engine_label})')
        
        # 构建完整文件路径
        from ..config import settings
        full_file_path = os.path.join(settings.UPLOAD_DIR, file_id)
        
        # 根据引擎选择执行不同的识别路径
        if use_vl:
            _update_task_status(task_id, progress=30, message='Running PaddleOCR-VL-1.6 recognition')
            result = ocr_service.process_image_vl(full_file_path)
        else:
            _update_task_status(task_id, progress=30, message='Running PP-StructureV3 analysis')
            result = ocr_service.process_image(full_file_path)
        
        # 更新进度: 保存结果
        _update_task_status(task_id, progress=80, message='Saving results')
        
        # 使用独立会话更新数据库记录
        with get_db_session() as db:
            question = db.query(Question).filter(Question.id == question_id).first()
            if question:
                # 版面分析主图（第一张 layout 图）作为 processed_image
                layout_images = result.get('layout_images', [])
                question.processed_image_path = (
                    layout_images[0] if layout_images
                    else result.get('original_image_path', '')
                )
                # 遮罩字段已废弃，保留列兼容性
                question.masked_image_path = None

                # Markdown 结构化文本
                question.ocr_result_md = result.get('markdown_content', '')

                # 完整 OCR 原始数据（含版面解析 + 图片路径列表 + md文件）
                question.ocr_raw_data = {
                    'parsing_results': result.get('parsing_results', []),
                    'layout_images': result.get('layout_images', []),
                    'extracted_images': result.get('extracted_images', []),
                    'markdown_file': result.get('markdown_file', ''),
                    'metadata': result.get('metadata', {}),
                }

                # 元数据
                question.question_metadata = result.get('metadata', {})
                question.status = "completed"

                processed_at_str = result.get('metadata', {}).get('processed_at')
                if processed_at_str:
                    question.processed_at = datetime.fromisoformat(processed_at_str)
            
            # 记录成功日志
            processing_time_ms = (time.time() - start_time) * 1000
            log = ProcessingLog(
                question_id=question_id,
                action="ocr_completed",
                level="INFO",
                message="OCR processing completed successfully",
                duration_ms=processing_time_ms
            )
            db.add(log)
        
        # 更新任务状态: 完成
        _update_task_status(
            task_id,
            status="completed",
            progress=100,
            message='Completed',
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        
        # 更新数据库记录为失败
        with get_db_session() as db:
            question = db.query(Question).filter(Question.id == question_id).first()
            if question:
                question.status = "failed"
                question.error_message = str(e)
            
            log = ProcessingLog(
                question_id=question_id,
                action="ocr_failed",
                level="ERROR",
                message=f"OCR processing failed: {str(e)}",
                duration_ms=processing_time_ms
            )
            db.add(log)
        
        # 更新任务状态: 失败
        _update_task_status(
            task_id,
            status="failed",
            progress=-1,
            message=f'Failed: {str(e)}',
            error=str(e),
            processing_time_ms=processing_time_ms
        )


def _update_task_status(
    task_id: str,
    status: str = None,
    progress: int = None,
    message: str = None,
    error: str = None,
    processing_time_ms: float = None
):
    """通过独立会话更新任务状态到数据库"""
    try:
        with get_db_session() as db:
            task = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
            if task:
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if error is not None:
                    task.error = error
                if processing_time_ms is not None:
                    task.processing_time_ms = processing_time_ms
    except Exception as e:
        # 状态更新失败不应中断主流程，仅记录日志
        from ..utils.logger import logger
        logger.warning(f"Failed to update task status for {task_id}: {e}")

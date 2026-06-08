from fastapi import APIRouter, BackgroundTasks, Depends
from typing import Optional
import uuid
import time

from ..services.ocr_service import ocr_service
from ..core.exceptions import OCRProcessingError
from ..schemas import OCRProcessRequest, OCRProcessResponse
from ..database import get_db
from ..models import Question, ProcessingLog
from sqlalchemy.orm import Session

router = APIRouter()

# 任务状态存储(生产环境应使用Redis)
task_status_store = {}


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
        db.commit()
        db.refresh(question)
        
        # 初始化任务状态
        task_status_store[task_id] = {
            'status': 'processing',
            'question_id': question.id,
            'progress': 0,
            'message': 'Processing started'
        }
        
        # 添加后台任务
        background_tasks.add_task(
            execute_ocr_processing,
            task_id=task_id,
            question_id=question.id,
            file_id=request.file_id,
            db=db
        )
        
        # 记录日志
        log = ProcessingLog(
            user_id=request.user_id,
            question_id=question.id,
            action="ocr_process",
            level="INFO",
            message=f"OCR processing started for file: {request.file_id}"
        )
        db.add(log)
        db.commit()
        
        return OCRProcessResponse(
            task_id=task_id,
            status="processing",
            message="OCR processing started successfully"
        )
        
    except Exception as e:
        raise OCRProcessingError(
            message=f"Failed to start OCR processing: {str(e)}",
            details={"error": str(e)}
        )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in task_status_store:
        return {"error": "Task not found"}
    
    return task_status_store[task_id]


async def execute_ocr_processing(
    task_id: str,
    question_id: int,
    file_id: str,
    db: Session
):
    """执行OCR处理的后台任务"""
    start_time = time.time()
    
    try:
        # 更新任务状态
        task_status_store[task_id]['progress'] = 10
        task_status_store[task_id]['message'] = 'Starting OCR processing'
        
        # 执行OCR处理
        task_status_store[task_id]['progress'] = 30
        task_status_store[task_id]['message'] = 'Performing layout analysis'
        
        result = ocr_service.process_image(file_id)
        
        # 更新进度
        task_status_store[task_id]['progress'] = 80
        task_status_store[task_id]['message'] = 'Saving results'
        
        # 更新数据库记录
        question = db.query(Question).filter(Question.id == question_id).first()
        if question:
            question.processed_image_path = result['processed_image_path']
            question.masked_image_path = result['processed_image_path']
            question.ocr_result_md = result['markdown_content']
            question.ocr_raw_data = result['ocr_raw_data']
            question.metadata = result['metadata']
            question.status = "completed"
            question.processed_at = result['metadata']['processed_at']
            
            db.commit()
        
        # 更新任务状态
        processing_time_ms = (time.time() - start_time) * 1000
        task_status_store[task_id]['progress'] = 100
        task_status_store[task_id]['message'] = 'Completed'
        task_status_store[task_id]['processing_time_ms'] = processing_time_ms
        
        # 记录成功日志
        log = ProcessingLog(
            question_id=question_id,
            action="ocr_completed",
            level="INFO",
            message=f"OCR processing completed successfully",
            duration_ms=processing_time_ms
        )
        db.add(log)
        db.commit()
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        
        # 更新任务状态为失败
        task_status_store[task_id]['progress'] = -1
        task_status_store[task_id]['message'] = f'Failed: {str(e)}'
        task_status_store[task_id]['error'] = str(e)
        
        # 更新数据库记录
        question = db.query(Question).filter(Question.id == question_id).first()
        if question:
            question.status = "failed"
            question.error_message = str(e)
            db.commit()
        
        # 记录错误日志
        log = ProcessingLog(
            question_id=question_id,
            action="ocr_failed",
            level="ERROR",
            message=f"OCR processing failed: {str(e)}",
            duration_ms=processing_time_ms
        )
        db.add(log)
        db.commit()

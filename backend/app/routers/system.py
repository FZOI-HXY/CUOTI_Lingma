from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import psutil
import time
import os
from datetime import datetime, timezone

from ..database import get_db
from ..models import Question, ProcessingLog
from ..schemas import SystemStatus, LogEntry
from ..config import settings
from ..utils.logger import logger

router = APIRouter()

# 应用启动时间
START_TIME = time.time()


def _get_disk_usage_percent() -> float:
    """跨平台获取系统盘使用率（兼容 Windows 和 Linux）"""
    try:
        if os.name == 'nt':
            # Windows: 使用系统盘符
            system_drive = os.environ.get('SystemDrive', 'C:') + os.sep
            return psutil.disk_usage(system_drive).percent
        else:
            return psutil.disk_usage('/').percent
    except Exception:
        return 0.0


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """获取系统状态信息"""
    try:
        # CPU和内存使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 磁盘使用率（跨平台兼容）
        disk_percent = _get_disk_usage_percent()
        
        # 统计错题数量
        total_questions = db.query(func.count(Question.id)).scalar() or 0
        
        # 计算运行时间
        uptime = time.time() - START_TIME
        
        return SystemStatus(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage_percent=disk_percent,
            active_tasks=0,  # TODO: 从任务队列获取
            total_questions=total_questions,
            uptime_seconds=uptime
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return SystemStatus(
            cpu_percent=0.0,
            memory_percent=0.0,
            disk_usage_percent=0.0,
            active_tasks=0,
            total_questions=0,
            uptime_seconds=time.time() - START_TIME
        )


@router.get("/logs")
async def get_processing_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: str = Query(None),
    action: str = Query(None),
    db: Session = Depends(get_db)
):
    """获取处理日志"""
    try:
        query = db.query(ProcessingLog)
        
        # 筛选条件
        if level:
            query = query.filter(ProcessingLog.level == level.upper())
        if action:
            query = query.filter(ProcessingLog.action == action)
        
        # 总数
        total = query.count()
        
        # 分页查询
        logs = query.order_by(ProcessingLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'items': [
                LogEntry(
                    id=log.id,
                    action=log.action,
                    level=log.level,
                    message=log.message,
                    duration_ms=log.duration_ms,
                    created_at=log.created_at
                )
                for log in logs
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing logs: {e}")
        return {'error': 'Failed to retrieve logs', 'items': []}


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """获取系统统计数据"""
    try:
        # 总错题数
        total_questions = db.query(func.count(Question.id)).scalar() or 0
        
        # 按状态统计
        status_counts = db.query(
            Question.status,
            func.count(Question.id)
        ).group_by(Question.status).all()
        
        status_dict = {status: count for status, count in status_counts}
        
        # 今日处理数（使用 timezone-aware UTC 时间）
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = db.query(func.count(Question.id)).filter(
            Question.created_at >= today_start
        ).scalar() or 0
        
        # 平均处理时间
        avg_duration = db.query(func.avg(ProcessingLog.duration_ms)).filter(
            ProcessingLog.action == "ocr_completed"
        ).scalar()
        
        return {
            'total_questions': total_questions,
            'status_distribution': status_dict,
            'today_processed': today_count,
            'avg_processing_time_ms': float(avg_duration) if avg_duration else 0,
            'storage_info': {
                'upload_dir_size': get_directory_size(settings.UPLOAD_DIR),
                'processed_dir_size': get_directory_size(settings.PROCESSED_DIR)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return {'error': 'Failed to retrieve statistics'}


def get_directory_size(path: str) -> int:
    """计算目录大小(字节)"""
    try:
        if not os.path.exists(path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        return total_size
        
    except Exception:
        return 0

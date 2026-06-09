from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class UploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str
    message: str = "File uploaded successfully"


class OCRProcessRequest(BaseModel):
    """OCR处理请求"""
    file_id: str
    user_id: Optional[int] = None
    lang: Optional[str] = "ch"
    use_gpu: Optional[bool] = False


class OCRProcessResponse(BaseModel):
    """OCR处理响应"""
    task_id: str
    status: str
    message: str = "Processing started"


class QuestionCreate(BaseModel):
    """创建错题请求"""
    original_image_path: str
    user_id: Optional[int] = None
    subject: Optional[str] = None
    tags: Optional[List[str]] = None


class QuestionResponse(BaseModel):
    """错题响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: Optional[int]
    original_image_path: str
    processed_image_path: Optional[str]
    masked_image_path: Optional[str]
    ocr_result_md: Optional[str]
    metadata: Optional[dict] = Field(None, alias='question_metadata')
    tags: Optional[List[str]]
    subject: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class QuestionListResponse(BaseModel):
    """错题列表响应"""
    total: int
    page: int
    page_size: int
    items: List[QuestionResponse]


class SystemStatus(BaseModel):
    """系统状态"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_tasks: int
    total_questions: int
    uptime_seconds: float


class LogEntry(BaseModel):
    """日志条目"""
    id: int
    action: str
    level: str
    message: str
    duration_ms: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

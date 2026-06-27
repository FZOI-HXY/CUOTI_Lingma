from pydantic import BaseModel, Field, ConfigDict, model_validator
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


class PDFPageTask(BaseModel):
    """PDF 单页任务信息"""
    page_number: int
    task_id: str
    question_id: int
    page_image_id: str


class PDFUploadResponse(BaseModel):
    """PDF 上传响应"""
    file_id: str
    filename: str
    total_pages: int
    pages: List[PDFPageTask]
    message: str = "PDF uploaded and processing started"


class OCRProcessRequest(BaseModel):
    """OCR处理请求"""
    file_id: str
    user_id: Optional[int] = None
    lang: Optional[str] = "ch"
    use_gpu: Optional[bool] = False
    use_vl: Optional[bool] = False  # True=使用 VL-1.6 增强模式，False=默认 PP-StructureV3


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
    masked_image_path: Optional[str] = None  # 已废弃，保留兼容
    ocr_result_md: Optional[str]
    metadata: Optional[dict] = Field(None, alias='question_metadata')
    tags: Optional[List[str]]
    subject: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    # 以下字段从 ocr_raw_data JSON 中解析
    layout_images: Optional[List[str]] = None
    extracted_images: Optional[List[str]] = None
    markdown_file: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def _extract_image_paths(cls, data):
        """从 ocr_raw_data JSON 自动提取版面图片和提取图片路径"""
        ocr_raw = None
        if isinstance(data, dict):
            ocr_raw = data.get('ocr_raw_data')
        elif hasattr(data, 'ocr_raw_data'):
            ocr_raw = getattr(data, 'ocr_raw_data', None)

        if isinstance(ocr_raw, dict):
            if isinstance(data, dict):
                if not data.get('layout_images'):
                    data['layout_images'] = ocr_raw.get('layout_images', [])
                if not data.get('extracted_images'):
                    data['extracted_images'] = ocr_raw.get('extracted_images', [])
                if not data.get('markdown_file'):
                    data['markdown_file'] = ocr_raw.get('markdown_file', '')
            else:
                # SQLAlchemy model → 转为 dict 并注入字段
                d = {c.name: getattr(data, c.name) for c in data.__table__.columns}
                d['layout_images'] = ocr_raw.get('layout_images', [])
                d['extracted_images'] = ocr_raw.get('extracted_images', [])
                d['markdown_file'] = ocr_raw.get('markdown_file', '')
                return d
        return data


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

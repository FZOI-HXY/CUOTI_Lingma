"""
报告下载 API
提供单题 Markdown/PDF 下载和批量导出功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import os

from ..database import get_db
from ..models import Question
from ..core.exceptions import NotFoundError
from ..services.report_service import report_service
from ..utils.logger import logger

router = APIRouter()


class BatchExportRequest(BaseModel):
    """批量导出请求"""
    question_ids: List[int]
    formats: Optional[List[str]] = None


def _question_to_dict(q: Question) -> dict:
    """将 SQLAlchemy Question 模型转为字典"""
    ocr_raw = q.ocr_raw_data or {}
    return {
        'id': q.id,
        'user_id': q.user_id,
        'original_image_path': q.original_image_path,
        'processed_image_path': q.processed_image_path,
        'ocr_result_md': q.ocr_result_md,
        'subject': q.subject,
        'tags': q.tags or [],
        'status': q.status,
        'created_at': str(q.created_at) if q.created_at else '',
        'processed_at': str(q.processed_at) if q.processed_at else '',
        'layout_images': ocr_raw.get('layout_images', []),
        'extracted_images': ocr_raw.get('extracted_images', []),
        'markdown_file': ocr_raw.get('markdown_file', ''),
    }


@router.get("/{question_id}/markdown")
async def download_markdown(
    question_id: int,
    db: Session = Depends(get_db)
):
    """下载单题 Markdown 报告"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise NotFoundError(message=f"Question {question_id} not found")

    try:
        q_dict = _question_to_dict(question)
        md_path = report_service.generate_markdown(q_dict)

        if not os.path.isfile(md_path):
            raise HTTPException(status_code=500, detail="Failed to generate markdown file")

        return FileResponse(
            path=md_path,
            media_type="text/markdown; charset=utf-8",
            filename=f"cuoti_{question_id}.md"
        )

    except Exception as e:
        logger.error(f"Failed to generate markdown for Q{question_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{question_id}/pdf")
async def download_pdf(
    question_id: int,
    db: Session = Depends(get_db)
):
    """下载单题 PDF 报告"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise NotFoundError(message=f"Question {question_id} not found")

    try:
        q_dict = _question_to_dict(question)
        pdf_path = report_service.generate_pdf(q_dict)

        if not os.path.isfile(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF file")

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"cuoti_{question_id}.pdf"
        )

    except Exception as e:
        logger.error(f"Failed to generate PDF for Q{question_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def download_batch(
    request: BatchExportRequest,
    db: Session = Depends(get_db)
):
    """
    批量导出报告（ZIP 包）
    - question_ids: 要导出的题目 ID 列表
    - formats: 导出格式，默认 ['markdown', 'pdf']
    """
    question_ids = request.question_ids
    formats = request.formats or ['markdown', 'pdf']

    if not question_ids:
        raise HTTPException(status_code=400, detail="question_ids cannot be empty")

    # 查询所有题目
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    if not questions:
        raise NotFoundError(message="No questions found for given IDs")

    try:
        q_dicts = [_question_to_dict(q) for q in questions]
        zip_path = report_service.generate_batch_zip(q_dicts, formats)

        if not os.path.isfile(zip_path):
            raise HTTPException(status_code=500, detail="Failed to generate ZIP file")

        zip_name = os.path.basename(zip_path)
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"cuoti_reports_{len(questions)}questions.zip"
        )

    except Exception as e:
        logger.error(f"Failed to generate batch report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

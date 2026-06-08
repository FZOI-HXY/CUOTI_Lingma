from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database import get_db
from ..models import Question, ProcessingLog
from ..schemas import QuestionResponse, QuestionListResponse, QuestionCreate
from ..core.exceptions import NotFoundError
from ..utils.logger import logger

router = APIRouter()


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question_data: QuestionCreate,
    db: Session = Depends(get_db)
):
    """创建新的错题记录"""
    try:
        question = Question(
            user_id=question_data.user_id,
            original_image_path=question_data.original_image_path,
            subject=question_data.subject,
            tags=question_data.tags,
            status="pending"
        )
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        logger.info(f"Question created: id={question.id}")
        return question
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=QuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    subject: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取错题列表(支持分页和筛选)"""
    try:
        query = db.query(Question)
        
        # 应用筛选条件
        if status:
            query = query.filter(Question.status == status)
        if subject:
            query = query.filter(Question.subject == subject)
        if user_id:
            query = query.filter(Question.user_id == user_id)
        
        # 总数
        total = query.count()
        
        # 分页
        questions = query.order_by(desc(Question.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        
        return QuestionListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=questions
        )
        
    except Exception as e:
        logger.error(f"Failed to list questions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """获取单个错题详情"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise NotFoundError(message=f"Question {question_id} not found")
    
    return question


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """删除错题记录"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise NotFoundError(message=f"Question {question_id} not found")
    
    try:
        db.delete(question)
        db.commit()
        logger.info(f"Question deleted: id={question_id}")
        return {"message": "Question deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{question_id}/tags")
async def update_question_tags(
    question_id: int,
    tags: List[str],
    db: Session = Depends(get_db)
):
    """更新错标题签"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise NotFoundError(message=f"Question {question_id} not found")
    
    try:
        question.tags = tags
        db.commit()
        db.refresh(question)
        logger.info(f"Question tags updated: id={question_id}")
        return question
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

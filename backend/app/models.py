from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    """用户信息表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # 关系
    questions = relationship("Question", back_populates="user")
    processing_logs = relationship("ProcessingLog", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Question(Base):
    """错题记录表"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # 文件路径
    original_image_path = Column(String(500), nullable=False)
    processed_image_path = Column(String(500), nullable=True)
    masked_image_path = Column(String(500), nullable=True)
    
    # OCR结果
    ocr_result_md = Column(Text, nullable=True)
    ocr_raw_data = Column(JSON, nullable=True)
    
    # 元数据
    metadata = Column(JSON, nullable=True)  # 存储版面分析结果、置信度等
    tags = Column(JSON, nullable=True)  # 标签列表
    subject = Column(String(50), nullable=True)  # 科目
    
    # 状态
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # 关系
    user = relationship("User", back_populates="questions")

    # 索引
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_status', 'status'),
    )

    def __repr__(self):
        return f"<Question(id={self.id}, status='{self.status}')>"


class ProcessingLog(Base):
    """处理日志表"""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True, index=True)
    
    # 日志内容
    action = Column(String(50), nullable=False)  # upload, process, save, delete, etc.
    level = Column(String(20), default="INFO")  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # 性能指标
    duration_ms = Column(Float, nullable=True)  # 处理耗时(毫秒)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = relationship("User", back_populates="processing_logs")
    question = relationship("Question")

    # 索引
    __table_args__ = (
        Index('idx_action_time', 'action', 'created_at'),
        Index('idx_level', 'level'),
    )

    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, action='{self.action}', level='{self.level}')>"


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), default="string")  # string, int, float, bool, json
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<SystemConfig(key='{self.config_key}')>"

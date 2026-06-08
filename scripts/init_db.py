"""
数据库初始化脚本
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import engine, Base
from app.models import User, Question, ProcessingLog, SystemConfig
from app.utils.logger import logger


def init_database():
    """初始化数据库"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # 创建默认配置
        from app.database import SessionLocal
        from app.models import SystemConfig
        
        db = SessionLocal()
        try:
            default_configs = [
                SystemConfig(config_key="ocr_lang", config_value="ch", description="OCR识别语言"),
                SystemConfig(config_key="ocr_use_gpu", config_value="false", description="是否使用GPU"),
                SystemConfig(config_key="max_file_size_mb", config_value="10", description="最大文件大小(MB)"),
            ]
            
            for config in default_configs:
                existing = db.query(SystemConfig).filter(SystemConfig.config_key == config.config_key).first()
                if not existing:
                    db.add(config)
            
            db.commit()
            logger.info("Default configurations created!")
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()
    print("Database initialization completed!")

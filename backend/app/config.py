from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置管理类"""
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8001  # 已从8000改为8001,避免端口残留问题
    DEBUG: bool = True
    
    # 数据库配置 - SQLite(默认)
    DB_FILE: str = "cuoti_system.db"
    
    # MySQL配置(如果使用MySQL,取消注释并设置)
    # DB_HOST: str = "localhost"
    # DB_PORT: int = 3306
    # DB_USER: str = "root"
    # DB_PASSWORD: str = "your_password"
    # DB_NAME: str = "cuoti_system"
    
    # OCR配置
    OCR_LANG: str = "ch"
    OCR_USE_GPU: bool = False
    OCR_DET_THRESH: float = 0.5
    OCR_REC_THRESH: float = 0.8
    
    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    
    # CORS配置
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        # SQLite配置
        if hasattr(self, 'DB_FILE') and self.DB_FILE:
            return f"sqlite:///{self.DB_FILE}"
        
        # MySQL配置(如果使用)
        # return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import List
import os


class Settings(BaseSettings):
    """应用配置管理类"""

    # 服务器配置
    HOST: str = "127.0.0.1"
    PORT: int = 8100
    DEBUG: bool = False

    # 数据库配置
    DB_BACKEND: str = "sqlite"  # "sqlite" or "mysql"
    DB_FILE: str = "cuoti_system.db"

    # MySQL配置(如果使用)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "your_password"
    DB_NAME: str = "cuoti_system"

    # OCR配置
    OCR_LANG: str = "ch"
    OCR_USE_GPU: bool = False
    OCR_DET_THRESH: float = 0.5
    OCR_REC_THRESH: float = 0.8

    # PaddleX 模型缓存目录（留空 → 默认使用 E:\Program Files\PP_Models）
    PADDLE_PDX_CACHE_HOME: str = ""

    # ── PaddleOCR-VL-1.6 增强模式配置 ──
    VL_ENABLED: bool = False                       # 是否启用 VL 增强模式
    VL_SERVER_PORT: int = 8101                     # llama-server 监听端口
    VL_SERVER_HOST: str = "127.0.0.1"            # llama-server 监听地址
    VL_CTX_SIZE: int = 4096                        # 上下文窗口大小
    VL_THREADS: int = 0                            # 推理线程数 (0=自动)
    VL_STARTUP_TIMEOUT: int = 120                  # llama-server 启动超时(秒)

    # 模型和工具路径
    VL_MODEL_DIR: str = r"E:\Program Files\PP_Models\official_models\PaddlePaddle\PaddleOCR-VL-1___6-GGUF"
    VL_LLAMA_CPP_DIR: str = ""                     # 留空 → 运行时自动推断
    # 以下路径可通过环境变量覆盖；留空时自动从 VL_MODEL_DIR / VL_LLAMA_CPP_DIR 推导
    VL_MODEL_PATH: str = ""
    VL_MMPROJ_PATH: str = ""
    VL_LLAMA_SERVER_PATH: str = ""

    @model_validator(mode='after')
    def _compute_vl_defaults(self):
        """Fill in VL path defaults from VL_MODEL_DIR when not set via env."""
        if not self.VL_MODEL_PATH:
            self.VL_MODEL_PATH = os.path.join(
                self.VL_MODEL_DIR, "PaddleOCR-VL-1.6-GGUF.gguf"
            )
        if not self.VL_MMPROJ_PATH:
            self.VL_MMPROJ_PATH = os.path.join(
                self.VL_MODEL_DIR, "PaddleOCR-VL-1.6-GGUF-mmproj.gguf"
            )
        if not self.VL_LLAMA_SERVER_PATH:
            if self.VL_LLAMA_CPP_DIR:
                self.VL_LLAMA_SERVER_PATH = os.path.join(
                    self.VL_LLAMA_CPP_DIR, "llama-server.exe"
                )
            else:
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(__file__))
                )
                self.VL_LLAMA_SERVER_PATH = os.path.join(
                    project_root, "tools", "llama-cpp", "llama-server.exe"
                )
        if not self.PADDLE_PDX_CACHE_HOME:
            self.PADDLE_PDX_CACHE_HOME = r"E:\Program Files\PP_Models"
        return self

    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    PROCESSED_DIR: str = "./processed"
    STORAGE_DIR: str = "./storage"   # 归档存储目录（按题目ID组织）
    MAX_FILE_SIZE: int = 10485760  # 10MB

    # PDF 处理配置
    PDF_DPI: int = 200                      # PDF 页面渲染 DPI（越高越清晰，越慢）
    PDF_MAX_PAGES: int = 30                 # 单个 PDF 最大处理页数
    PDF_MAX_FILE_SIZE: int = 52428800       # PDF 文件最大 50MB

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # CORS配置
    CORS_ORIGINS: str = "http://127.0.0.1:8100,http://localhost:8100,tauri://localhost"

    # API认证密钥（留空则不启用认证，用于开发环境）
    API_KEY: str = ""

    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        if self.DB_BACKEND == "mysql":
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return f"sqlite:///{self.DB_FILE}"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

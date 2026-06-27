from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time

from .config import settings
from .core.exceptions import AppException
from .utils.logger import setup_logger, logger
from .database import engine, Base, get_db_session
from .models import TaskStatus
from .routers import upload, ocr, questions, system, reports


logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting Cuoti Management System...")
    
    # 导入所有模型，确保它们被注册到Base.metadata
    from . import models  # noqa: F401
    
    # 创建数据库表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    # 恢复中断的任务状态（服务重启后，将processing状态的任务标记为failed）
    try:
        with get_db_session() as db:
            stale_tasks = db.query(TaskStatus).filter(
                TaskStatus.status == "processing"
            ).all()
            for task in stale_tasks:
                task.status = "failed"
                task.message = "Task interrupted by server restart"
                task.error = "Server was restarted while task was processing"
            if stale_tasks:
                logger.warning(f"Marked {len(stale_tasks)} stale task(s) as failed after restart")
    except Exception as e:
        logger.warning(f"Failed to recover stale tasks (table may not exist yet): {e}")
    
    # 创建必要的目录
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    logger.info("Required directories created")
    
    # 初始化 VL 增强模式（如果启用）
    if settings.VL_ENABLED:
        try:
            from .services.vl_service import vl_service
            vl_service.initialize()
            if vl_service.is_available:
                logger.info("VL enhancement mode: READY")
            else:
                logger.warning("VL enhancement mode: configured but not available")
        except Exception as e:
            logger.warning(f"VL enhancement mode init failed: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down Cuoti Management System...")
    
    # 关闭 VL 服务
    try:
        from .services.vl_service import vl_service
        vl_service.shutdown()
    except Exception:
        pass


# 创建FastAPI应用
app = FastAPI(
    title="Cuoti Management System API",
    description="错题管理系统后端API - 集成PaddleOCR实现智能OCR处理",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS — 使用配置白名单，仅允许受信任的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key 认证中间件（C1: 路由认证 + C2: 静态文件保护）
@app.middleware("http")
async def api_key_auth_middleware(request, call_next):
    """
    API Key authentication middleware.
    - Skips auth for public endpoints (health, docs, root).
    - If API_KEY is empty, skips all auth (development mode).
    - If API_KEY is set, requires Authorization: Bearer {key} on /api/* and static file routes.
    """
    path = request.url.path

    # Public endpoints that never require auth
    public_paths = {"/health", "/", "/docs", "/openapi.json", "/redoc"}
    if path in public_paths:
        return await call_next(request)

    # Development mode: no API_KEY configured, skip all auth
    if not settings.API_KEY:
        return await call_next(request)

    # Routes that require authentication: /api/* and static file mounts
    static_prefixes = ("/uploads/", "/processed/", "/storage/")
    requires_auth = path.startswith("/api/") or any(path.startswith(p) for p in static_prefixes)

    if requires_auth:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:] != settings.API_KEY:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    return await call_next(request)


# 全局异常处理器
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed", "details": exc.errors()}
    )


# 注册路由
app.include_router(upload.router, prefix="/api/v1/upload", tags=["文件上传"])
app.include_router(ocr.router, prefix="/api/v1/ocr", tags=["OCR处理"])
app.include_router(questions.router, prefix="/api/v1/questions", tags=["错题管理"])
app.include_router(system.router, prefix="/api/v1/system", tags=["系统监控"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["报告下载"])

# 挂载静态文件目录（用于客户端访问上传和处理的图片）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/processed", StaticFiles(directory=settings.PROCESSED_DIR), name="processed")
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")


# 健康检查接口
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


# 根路径
@app.get("/")
async def root():
    return {
        "message": "Welcome to Cuoti Management System API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

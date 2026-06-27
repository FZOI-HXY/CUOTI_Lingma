from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from .config import settings
from .utils.logger import logger

# 使用config中的database_url
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},  # SQLite需要
    pool_pre_ping=True,
    pool_size=10 if not DATABASE_URL.startswith("sqlite") else None,
    max_overflow=20 if not DATABASE_URL.startswith("sqlite") else None,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类"""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI依赖注入用的数据库会话生成器（仅限请求生命周期内使用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    独立的数据库会话上下文管理器。
    适用于后台任务、Celery任务等脱离HTTP请求生命周期的场景。
    自动提交/回滚，并确保会话关闭。
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

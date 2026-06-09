"""
修复数据库中的时间戳 - 将UTC时间转换为本地时间(北京时间 UTC+8)
"""
import sys
import os
from datetime import timedelta

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal, engine
from app.models import User, Question, ProcessingLog
from sqlalchemy import inspect

def fix_timestamps():
    """修复所有表中的时间戳"""
    db = SessionLocal()
    
    try:
        # 检查表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"发现以下表: {tables}")
        
        # 时区偏移: UTC+8
        offset = timedelta(hours=8)
        
        # 修复 users 表
        if 'users' in tables:
            users = db.query(User).all()
            print(f"\n修复 Users 表 ({len(users)} 条记录):")
            for user in users:
                if user.created_at:
                    old_time = user.created_at
                    user.created_at = old_time + offset
                    print(f"  User {user.id}: {old_time} -> {user.created_at}")
                
                if user.updated_at:
                    old_time = user.updated_at
                    user.updated_at = old_time + offset
        
        # 修复 questions 表
        if 'questions' in tables:
            questions = db.query(Question).all()
            print(f"\n修复 Questions 表 ({len(questions)} 条记录):")
            for question in questions:
                if question.created_at:
                    old_time = question.created_at
                    question.created_at = old_time + offset
                    print(f"  Question {question.id}: {old_time} -> {question.created_at}")
                
                if question.updated_at:
                    old_time = question.updated_at
                    question.updated_at = old_time + offset
                
                if question.processed_at:
                    old_time = question.processed_at
                    question.processed_at = old_time + offset
        
        # 修复 processing_logs 表
        if 'processing_logs' in tables:
            logs = db.query(ProcessingLog).all()
            print(f"\n修复 ProcessingLogs 表 ({len(logs)} 条记录):")
            for log in logs:
                if log.created_at:
                    old_time = log.created_at
                    log.created_at = old_time + offset
                    print(f"  Log {log.id}: {old_time} -> {log.created_at}")
        
        # 提交更改
        db.commit()
        print("\n✅ 所有时间戳已修复!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("修复数据库时间戳 - UTC 转北京时间 (UTC+8)")
    print("=" * 60)
    fix_timestamps()

"""
快速测试脚本 - 验证系统是否可以正常启动
"""
import sys
import os
from pathlib import Path

# 添加backend目录到路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_imports():
    """测试导入"""
    print("🔍 测试模块导入...")
    
    try:
        from app.database import engine, DATABASE_URL
        print(f"✅ 数据库模块导入成功")
        print(f"   数据库URL: {DATABASE_URL}")
        
        # 检查是否为SQLite
        if DATABASE_URL.startswith('sqlite'):
            db_file = DATABASE_URL.replace('sqlite:///', '')
            print(f"   SQLite文件: {os.path.abspath(db_file)}")
            if os.path.exists(db_file):
                print(f"   ✅ 数据库文件存在")
            else:
                print(f"   ⚠️  数据库文件不存在,需要初始化")
        
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False
    
    try:
        from app.models import User, Question, ProcessingLog, SystemConfig
        print(f"✅ 数据模型导入成功")
    except Exception as e:
        print(f"❌ 数据模型导入失败: {e}")
        return False
    
    try:
        from app.config import settings
        print(f"✅ 配置模块导入成功")
        print(f"   HOST: {settings.HOST}")
        print(f"   PORT: {settings.PORT}")
    except Exception as e:
        print(f"❌ 配置模块导入失败: {e}")
        return False
    
    return True


def test_database():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ 数据库连接成功!")
            
        # 检查表是否存在
        from app.database import SessionLocal
        from app.models import Base
        
        db = SessionLocal()
        try:
            # 尝试查询
            from app.models import SystemConfig
            configs = db.query(SystemConfig).all()
            print(f"✅ 数据库表存在,找到 {len(configs)} 条配置")
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n提示: 运行以下命令初始化数据库:")
        print("  python scripts/init_db.py")
        return False


def test_dependencies():
    """测试关键依赖"""
    print("\n🔍 测试关键依赖...")
    
    dependencies = [
        ("FastAPI", "fastapi"),
        ("SQLAlchemy", "sqlalchemy"),
        ("Pydantic", "pydantic"),
        ("OpenCV", "cv2"),
        ("Pillow", "PIL"),
        ("NumPy", "numpy"),
        ("Loguru", "loguru"),
    ]
    
    all_ok = True
    for name, module in dependencies:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name} - {e}")
            all_ok = False
    
    return all_ok


def main():
    """主函数"""
    print("="*60)
    print("🧪 系统启动前测试")
    print("="*60)
    print()
    
    results = []
    
    # 测试1: 依赖
    results.append(("依赖检查", test_dependencies()))
    
    # 测试2: 导入
    results.append(("模块导入", test_imports()))
    
    # 测试3: 数据库
    results.append(("数据库连接", test_database()))
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 所有测试通过!系统可以启动。")
        print("\n启动命令:")
        print("  .\\start.bat          # 一键启动")
        print("  python manage.py start  # Python脚本启动")
    else:
        print("\n⚠️  部分测试失败,请修复后再启动。")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

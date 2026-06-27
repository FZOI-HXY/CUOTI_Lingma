"""
服务启动脚本
"""
import subprocess
import sys
import os
import time


def start_backend():
    """启动后端服务"""
    print("=" * 60)
    print("Starting Backend Service...")
    print("=" * 60)
    
    backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
    os.chdir(backend_dir)
    
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "app.main"],
            cwd=backend_dir
        )
        print(f"Backend started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start backend: {e}")
        return None


def start_frontend():
    """启动前端应用"""
    print("\n" + "=" * 60)
    print("Starting Frontend Application...")
    print("=" * 60)
    
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    
    try:
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=frontend_dir
        )
        print(f"Frontend started with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Failed to start frontend: {e}")
        return None


def main():
    """主函数"""
    print("\n🚀 Cuoti Management System - Starting Services\n")
    
    # 启动后端
    backend_process = start_backend()
    
    if not backend_process:
        print("❌ Failed to start backend service")
        sys.exit(1)
    
    # 等待后端启动
    print("\n⏳ Waiting for backend to start...")
    time.sleep(3)
    
    # 启动前端
    frontend_process = start_frontend()
    
    if not frontend_process:
        print("❌ Failed to start frontend application")
        backend_process.terminate()
        sys.exit(1)
    
    print("\n✅ All services started successfully!")
    print("\nPress Ctrl+C to stop all services\n")
    
    try:
        # 等待进程结束
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Services stopped")


if __name__ == "__main__":
    main()

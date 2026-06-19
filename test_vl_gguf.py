"""
PaddleOCR-VL-1.6 GGUF CPU 推理测试脚本
用法: python test_vl_gguf.py [图片路径]
"""
import subprocess
import sys
import os
import time
import requests

# === 配置 ===
LLAMA_SERVER = os.path.join(os.path.dirname(__file__), "tools", "llama-cpp", "llama-server.exe")
MODEL_DIR = r"E:\Program Files\PP_Models\official_models\PaddlePaddle\PaddleOCR-VL-1___6-GGUF"
MODEL_GGUF = os.path.join(MODEL_DIR, "PaddleOCR-VL-1.6-GGUF.gguf")
MMPROJ_GGUF = os.path.join(MODEL_DIR, "PaddleOCR-VL-1.6-GGUF-mmproj.gguf")
SERVER_PORT = 8101
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}/v1"


def check_files():
    """检查模型文件和 llama-server 是否存在"""
    for name, path in [("llama-server", LLAMA_SERVER), ("GGUF 模型", MODEL_GGUF), ("多模态投影", MMPROJ_GGUF)]:
        if not os.path.exists(path):
            print(f"[错误] {name} 不存在: {path}")
            return False
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"[OK] {name}: {path} ({size_mb:.1f} MB)")
    return True


def start_server():
    """启动 llama-server"""
    cmd = [
        LLAMA_SERVER,
        "-m", MODEL_GGUF,
        "--mmproj", MMPROJ_GGUF,
        "--port", str(SERVER_PORT),
        "--host", "0.0.0.0",
        "--temp", "0",
    ]
    print(f"\n[启动] llama-server...")
    print(f"  命令: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc


def wait_for_server(timeout=120):
    """等待 server 就绪"""
    print(f"[等待] 服务器启动中 (最多 {timeout} 秒)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"http://127.0.0.1:{SERVER_PORT}/health", timeout=2)
            if r.status_code == 200:
                print(f"[OK] 服务器就绪! (耗时 {time.time()-start:.1f} 秒)")
                return True
        except Exception:
            pass
        time.sleep(2)
    print(f"[超时] 服务器未在 {timeout} 秒内启动")
    return False


def test_paddleocr_vl(image_path):
    """用 PaddleOCRVL 测试"""
    print(f"\n[测试] PaddleOCR-VL-1.6 (llama-cpp-server 后端)")
    print(f"  图片: {image_path}")

    from paddleocr import PaddleOCRVL
    pipeline = PaddleOCRVL(
        pipeline_version="v1.6",
        vl_rec_backend="llama-cpp-server",
        vl_rec_server_url=SERVER_URL,
    )
    output = pipeline.predict(image_path)
    for res in output:
        res.print()
        res.save_to_json(save_path="output")
        res.save_to_markdown(save_path="output")
    print("\n[完成] 结果已保存到 output/ 目录")


def test_llama_cli(image_path):
    """用 llama-cli 直接测试（备选方案）"""
    llama_cli = os.path.join(os.path.dirname(LLAMA_SERVER), "llama-cli.exe")
    if not os.path.exists(llama_cli):
        print("[跳过] llama-cli 不存在")
        return
    cmd = [
        llama_cli,
        "-m", MODEL_GGUF,
        "--mmproj", MMPROJ_GGUF,
        "-p", "OCR:",
        "--image", image_path,
    ]
    print(f"\n[测试] llama-cli 直接推理")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    print("STDOUT:", result.stdout[:2000] if result.stdout else "(空)")
    if result.stderr:
        print("STDERR:", result.stderr[:500])


if __name__ == "__main__":
    # 默认用 PaddleOCR 自带 demo 图片
    image = sys.argv[1] if len(sys.argv) > 1 else \
        "https://paddle-model-ecology.bj.bcebos.com/paddlex/imgs/demo_image/paddleocr_vl_demo.png"

    print("=" * 60)
    print("PaddleOCR-VL-1.6 GGUF CPU 推理测试")
    print("=" * 60)

    # 1. 检查文件
    if not check_files():
        sys.exit(1)

    # 2. 启动 server
    proc = start_server()
    try:
        if not wait_for_server():
            # 打印 stderr 帮助调试
            proc.terminate()
            _, stderr = proc.communicate(timeout=5)
            print("\n[调试] 服务器 stderr:")
            print(stderr.decode("utf-8", errors="replace")[:2000] if stderr else "(空)")
            sys.exit(1)

        # 3. 测试 PaddleOCR VL
        test_paddleocr_vl(image)

        # 4. 备选: llama-cli 直接测试
        if os.path.exists(image):  # llama-cli 只支持本地文件
            test_llama_cli(image)

    finally:
        print("\n[清理] 关闭 llama-server...")
        proc.terminate()
        proc.wait(timeout=5)
        print("[完成]")

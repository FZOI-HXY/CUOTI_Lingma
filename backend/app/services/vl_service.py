"""
PaddleOCR-VL-1.6 视觉语言模型服务

管理 llama-server 的生命周期（启动、健康检查、关闭），
并通过 PaddleOCRVL 接口调用 VL 模型进行高精度文档识别。

作为 PP-StructureV3 的增强模式使用，不替代原有管线。
"""

import os
import time
import subprocess
import signal
import base64
import json
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime, timezone

import requests

from ..config import settings
from ..utils.logger import logger


class VLService:
    """PaddleOCR-VL-1.6 服务封装

    职责:
      1. 管理 llama-server.exe 子进程（启动 / 健康检查 / 关闭）
      2. 提供 process_image() 接口，返回与 OCRService 兼容的结果格式
    """

    def __init__(self):
        self._server_proc: Optional[subprocess.Popen] = None
        self._log_fh = None  # 日志文件句柄
        self._available = False
        self._initialized = False

    # ──────────────────────────────────────────────────────
    # 属性
    # ──────────────────────────────────────────────────────
    @property
    def server_url(self) -> str:
        return f"http://127.0.0.1:{settings.VL_SERVER_PORT}/v1"

    @property
    def health_url(self) -> str:
        return f"http://127.0.0.1:{settings.VL_SERVER_PORT}/health"

    @property
    def is_running(self) -> bool:
        """llama-server 进程是否仍在运行（含外部启动检测）"""
        # 自己管理的进程
        if self._server_proc is not None:
            return self._server_proc.poll() is None
        # 外部启动的进程：通过健康检查探测
        try:
            r = requests.get(self.health_url, timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        """VL 服务是否可用（配置启用 + 服务运行中）"""
        if not settings.VL_ENABLED:
            return False
        if not self.is_running:
            return False
        try:
            r = requests.get(self.health_url, timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    # ──────────────────────────────────────────────────────
    # 生命周期管理
    # ──────────────────────────────────────────────────────
    def initialize(self):
        """启动 llama-server（如果配置启用且尚未启动）"""
        if self._initialized and self.is_running:
            return

        if not settings.VL_ENABLED:
            logger.info("VL enhancement mode is disabled in config")
            self._initialized = True
            return

        # 检查必要文件
        llama_server = settings.VL_LLAMA_SERVER_PATH
        model_gguf = settings.VL_MODEL_PATH
        mmproj_gguf = settings.VL_MMPROJ_PATH

        # ── 先探测外部启动的 llama-server（如 start.bat 启动的） ──
        try:
            r = requests.get(self.health_url, timeout=3)
            if r.status_code == 200:
                self._available = True
                self._initialized = True
                logger.info(
                    f"External llama-server detected on port "
                    f"{settings.VL_SERVER_PORT}"
                )
                return
        except (requests.ConnectionError, requests.Timeout):
            pass  # 没有外部服务，继续自行启动

        for label, path in [
            ("llama-server", llama_server),
            ("GGUF model", model_gguf),
            ("mmproj GGUF", mmproj_gguf),
        ]:
            if not os.path.isfile(path):
                logger.warning(f"VL disabled: {label} not found at {path}")
                self._initialized = True
                return

        # 启动 llama-server
        try:
            logger.info(f"Starting llama-server on port {settings.VL_SERVER_PORT}...")

            cmd = [
                llama_server,
                "-m", model_gguf,
                "--mmproj", mmproj_gguf,
                "--port", str(settings.VL_SERVER_PORT),
                "--host", settings.VL_SERVER_HOST,
                "--temp", "0",
                "-ngl", "0",  # CPU only
            ]

            # 可选参数: 上下文长度
            if settings.VL_CTX_SIZE > 0:
                cmd.extend(["-c", str(settings.VL_CTX_SIZE)])

            # 可选参数: 线程数
            if settings.VL_THREADS > 0:
                cmd.extend(["-t", str(settings.VL_THREADS)])

            # 静默模式：把 stdout/stderr 写入日志文件
            log_path = os.path.join(settings.LOG_DIR, "llama-server.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            self._log_fh = open(log_path, "a", encoding="utf-8")

            self._server_proc = subprocess.Popen(
                cmd,
                stdout=self._log_fh,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
                if os.name == "nt" else 0,
            )

            # 等待就绪
            if self._wait_for_server(timeout=settings.VL_STARTUP_TIMEOUT):
                self._available = True
                logger.info(
                    f"llama-server started (PID={self._server_proc.pid}), "
                    f"port={settings.VL_SERVER_PORT}"
                )
            else:
                logger.error(
                    f"llama-server failed to start within "
                    f"{settings.VL_STARTUP_TIMEOUT}s"
                )
                self._stop_server()

        except Exception as e:
            logger.error(f"Failed to start llama-server: {e}")
            self._stop_server()

        self._initialized = True

    def shutdown(self):
        """优雅关闭 llama-server"""
        self._stop_server()
        logger.info("VL service shut down")

    # ──────────────────────────────────────────────────────
    # VL 推理接口
    # ──────────────────────────────────────────────────────
    def process_image(self, image_path: str) -> Dict:
        """使用 VL 模型处理图片，返回与 OCRService.process_image() 兼容的格式

        通过 PaddleOCRVL 调用 llama-server 完成识别。
        """
        start_time = time.time()

        if not self.is_available:
            raise RuntimeError(
                "VL service is not available. "
                "Please check llama-server is running."
            )

        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        logger.info(f"VL processing: {image_path}")

        try:
            # 方式一：使用 PaddleOCRVL（推荐）
            result = self._process_via_paddleocr_vl(image_path)
        except ImportError:
            logger.warning("PaddleOCRVL not available, falling back to direct API")
            result = self._process_via_direct_api(image_path)

        processing_time_ms = (time.time() - start_time) * 1000

        # 构造与 OCRService 兼容的返回格式
        markdown_content = result.get("markdown", "")
        parsing_results = result.get("blocks", [])

        metadata = {
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "language": settings.OCR_LANG,
            "processing_time_ms": processing_time_ms,
            "block_count": len(parsing_results),
            "image_count": 0,
            "layout_image_count": 0,
            "engine": "PaddleOCR-VL-1.6",
        }

        # 保存 Markdown
        markdown_file = self._save_markdown(markdown_content, image_path)

        logger.info(
            f"VL done in {processing_time_ms:.0f}ms, "
            f"{len(parsing_results)} blocks"
        )

        return {
            "markdown_content": markdown_content,
            "markdown_file": markdown_file,
            "layout_images": [],          # VL 不生成版面分析图
            "extracted_images": [],       # VL 不提取嵌入图片
            "parsing_results": parsing_results,
            "original_image_path": image_path,
            "metadata": metadata,
            "ocr_raw_data": {
                "parsing_results": parsing_results,
                "layout_images": [],
                "extracted_images": [],
                "markdown_file": markdown_file,
                "metadata": metadata,
            },
            "processed_image_path": image_path,
        }

    # ──────────────────────────────────────────────────────
    # 内部实现
    # ──────────────────────────────────────────────────────
    def _process_via_paddleocr_vl(self, image_path: str) -> Dict:
        """通过 PaddleOCRVL 调用（需要 paddleocr >= 3.6.0）"""
        from paddleocr import PaddleOCRVL

        pipeline = PaddleOCRVL(
            pipeline_version="v1.6",
            vl_rec_backend="llama-cpp-server",
            vl_rec_server_url=self.server_url,
        )

        output = pipeline.predict(image_path)

        markdown_parts = []
        blocks = []

        for res in output:
            # 尝试获取 markdown
            md = getattr(res, "markdown", None)
            if md is None and hasattr(res, "to_markdown"):
                md = res.to_markdown()
            if md:
                if isinstance(md, dict):
                    markdown_parts.append(md.get("markdown_texts", str(md)))
                else:
                    markdown_parts.append(str(md))

            # 尝试保存到 json
            try:
                res.save_to_json(save_path=os.path.join(
                    settings.PROCESSED_DIR, "vl_output"
                ))
            except Exception as e:
                logger.debug(f"save_to_json skipped: {e}")

        markdown_content = "\n\n".join(markdown_parts) if markdown_parts else ""

        return {
            "markdown": markdown_content,
            "blocks": blocks,
        }

    def _process_via_direct_api(self, image_path: str) -> Dict:
        """直接调用 llama-server 的 OpenAI-compatible API"""

        # 读取图片并编码为 base64
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # 推断 MIME 类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/png")

        # 构造 OpenAI vision 请求
        payload = {
            "model": "paddleocr-vl",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{img_b64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "请对这张图片进行OCR识别，"
                                "输出所有文字内容，保留原始排版格式。"
                                "如果有表格请用Markdown表格格式输出，"
                                "如果有公式请用LaTeX格式输出。"
                            ),
                        },
                    ],
                }
            ],
            "temperature": 0,
            "max_tokens": 4096,
        }

        url = f"{self.server_url}/chat/completions"
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()

        data = resp.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        return {
            "markdown": content,
            "blocks": [],
        }

    def _wait_for_server(self, timeout: int = 120) -> bool:
        """轮询等待 llama-server 健康检查通过"""
        start = time.time()
        while time.time() - start < timeout:
            # 检查进程是否已退出
            if self._server_proc and self._server_proc.poll() is not None:
                logger.error(
                    f"llama-server exited with code "
                    f"{self._server_proc.returncode}"
                )
                return False

            try:
                r = requests.get(self.health_url, timeout=2)
                if r.status_code == 200:
                    return True
            except (requests.ConnectionError, requests.Timeout):
                pass

            time.sleep(2)

        return False

    def _stop_server(self):
        """停止 llama-server 子进程"""
        if self._server_proc is not None:
            try:
                if self._server_proc.poll() is None:
                    # Windows: 发送 CTRL_BREAK_EVENT → 再 terminate
                    if os.name == "nt":
                        self._server_proc.terminate()
                    else:
                        self._server_proc.send_signal(signal.SIGTERM)

                    try:
                        self._server_proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning("llama-server did not exit, killing")
                        self._server_proc.kill()
                        self._server_proc.wait(timeout=5)

                    logger.info("llama-server stopped")
            except Exception as e:
                logger.warning(f"Error stopping llama-server: {e}")
            finally:
                self._server_proc = None
                self._available = False
                # 关闭日志文件句柄
                if self._log_fh is not None:
                    try:
                        self._log_fh.close()
                    except Exception:
                        pass
                    self._log_fh = None

    def _save_markdown(self, markdown_content: str, image_path: str) -> str:
        """保存 VL 输出的 Markdown 文件"""
        markdown_dir = os.path.join(settings.PROCESSED_DIR, "markdown")
        os.makedirs(markdown_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        md_path = os.path.join(markdown_dir, f"{base_name}_vl.md")

        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logger.info(f"Saved VL markdown to: {md_path}")
            return md_path
        except Exception as e:
            logger.warning(f"Failed to save VL markdown: {e}")
            return ""


# 全局 VL 服务实例
vl_service = VLService()

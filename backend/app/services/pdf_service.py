"""
PDF 处理服务 —— 将 PDF 页面渲染为图片，供 OCR 管线使用。
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

from ..config import settings
from ..utils.logger import logger


class PDFService:
    """PDF 文件处理：提取页面为 PNG 图片"""

    def get_page_count(self, pdf_path: str) -> int:
        """获取 PDF 总页数"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get PDF page count: {e}")
            raise

    def render_pages_to_images(
        self,
        pdf_path: str,
        output_dir: str,
        dpi: int = None,
        max_pages: int = None,
        file_prefix: str = None,
    ) -> List[Dict]:
        """
        将 PDF 的每一页渲染为 PNG 图片。

        Returns:
            列表，每项包含:
            - page_number: 页码（从 1 开始）
            - image_filename: 生成的 PNG 文件名
            - image_path: 完整的文件路径
        """
        if dpi is None:
            dpi = settings.PDF_DPI
        if max_pages is None:
            max_pages = settings.PDF_MAX_PAGES
        if file_prefix is None:
            file_prefix = datetime.now().strftime("%Y%m%d_%H%M%S")

        os.makedirs(output_dir, exist_ok=True)

        try:
            import fitz  # PyMuPDF

            with fitz.open(pdf_path) as doc:
                total_pages = min(len(doc), max_pages)
                results = []

                # 将 DPI 转换为缩放矩阵（默认 72 DPI → 目标 DPI）
                zoom = dpi / 72
                matrix = fitz.Matrix(zoom, zoom)

                for page_idx in range(total_pages):
                    page = doc[page_idx]
                    pix = page.get_pixmap(matrix=matrix)

                    # 生成唯一文件名
                    unique_id = uuid.uuid4().hex[:8]
                    image_filename = f"{file_prefix}_p{page_idx + 1}_{unique_id}.png"
                    image_path = os.path.join(output_dir, image_filename)

                    pix.save(image_path)
                    pix = None  # 释放内存

                    results.append({
                        "page_number": page_idx + 1,
                        "image_filename": image_filename,
                        "image_path": image_path,
                    })

                    logger.debug(
                        f"PDF page {page_idx + 1}/{total_pages} rendered: {image_filename}"
                    )

            logger.info(
                f"PDF rendered: {total_pages} pages from {os.path.basename(pdf_path)}"
            )
            return results

        except Exception as e:
            logger.error(f"PDF page rendering failed: {e}")
            raise


# 全局单例
pdf_service = PDFService()
